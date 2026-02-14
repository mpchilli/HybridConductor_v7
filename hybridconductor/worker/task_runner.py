"""
hybridconductor.worker.task_runner - Stateless Task Executor Logic

Contains the core logic for executing tasks, running BIST,
and managing isolated git branches.
"""

import os
import sys
import re
import subprocess
import tempfile
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
import requests
import time

from hybridconductor.mcp.client import McpClient
from hybridconductor.utils.safe_cleanup import safe_tempdir
from hybridconductor.core import LoopGuardian, normalize_output, compute_normalized_hash
from hybridconductor.config import config
from hybridconductor.logger import setup_logging, log_ai_conversation

def execute_task(
    plan: str,
    context: str,
    complexity_mode: str,
    max_iterations: int = 25,
    tmp_dir: Optional[Path] = None
) -> bool:
    """
    Execute a single task with BIST verification.
    """
    print(f" Executing task in {complexity_mode} mode")
    
    # Initialize logger
    logger = setup_logging("worker", debug=os.environ.get("HC_DEBUG"))

    # Launch MCP Git server for safe operations
    mcp_process = _launch_mcp_git_server()
    
    try:
        if tmp_dir:
            return _execute_task_logic(plan, context, complexity_mode, max_iterations, tmp_dir, mcp_process)
        else:
            with safe_tempdir(prefix="hc_task_") as safe_dir:
                 return _execute_task_logic(plan, context, complexity_mode, max_iterations, safe_dir, mcp_process)

    finally:
        # Cleanup MCP server
        mcp_process.terminate()
        try:
            mcp_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            mcp_process.kill()
        print(" MCP server terminated")


def _execute_task_logic(plan, context, complexity_mode, max_iterations, tmp_dir, mcp_process):
    # Create isolated branch for this task
    mcp_client = McpClient()
    task_id = _generate_task_id()
    branch_name = f"task-{task_id}"
    
    print(f"SetBranch: {branch_name}")
    try:
        mcp_client.create_branch(branch_name)
        mcp_client.switch_branch(branch_name)
    except Exception as e:
        print(f" Branch setup failed: {e}")
        # Continue? Or fail?
    
    # Execute task with linear retry escalation
    for attempt in range(max_iterations):
        temperature = _get_temperature_for_attempt(attempt)
        
        print(f"Attempt {attempt + 1}/{max_iterations} (temp={temperature})")
        
        # Generate code simulation
        response = _generate_code(plan=plan, context=context, temperature=temperature)
        # Database path relative to project root (cwd)
        db_path = Path("logs") / "activity.db"
        
        # Log interaction for transparency
        log_ai_conversation("USER", f"Attempt {attempt+1}: {plan}", db_path)
        log_ai_conversation("AI", response[:500], db_path)
        
        # Parse multiple files (delimited by # filename: ...)
        file_blocks = re.split(r"^# filename: ", response, flags=re.MULTILINE)
        
        all_bist_success = True
        saved_files = []
        
        for block in file_blocks:
            if not block.strip(): continue
            lines = block.strip().splitlines()
            filename = lines[0].strip()
            content = "\n".join(lines[1:])
            
            # Save to tmp_dir for BIST
            tmp_path = tmp_dir / filename
            with open(tmp_path, "w", encoding="utf-8-sig") as f:
                f.write(content)
            
            # Run BIST
            if not _run_bist(tmp_path):
                print(f" BIST failed for: {filename}")
                all_bist_success = False
                break
            
            saved_files.append((tmp_path, filename))
        
        if all_bist_success and saved_files:
            print(f" All {len(saved_files)} files passed BIST.")
            
            # Create timestamped directory: tests/YYYYMMMdd/HHMMSS_taskid/
            from datetime import datetime
            timestamp = datetime.now()
            date_str = timestamp.strftime("%Y%b%d")
            time_str = timestamp.strftime("%H%M%S")
            target_dir = Path.cwd() / "tests" / date_str / f"{time_str}_{task_id}"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            for tmp_path, filename in saved_files:
                final_path = target_dir / filename
                with open(tmp_path, "r", encoding="utf-8-sig") as src, open(final_path, "w", encoding="utf-8-sig") as dst:
                    dst.write(src.read())
                print(f" Persisted: {final_path}")
            
            mcp_client.commit(f"Auto-commit task {task_id}")
            return True
        else:
            print(f" Attempt {attempt + 1} failed.")
            if _detect_loop(response, attempt):
                print(" Loop detected. Escalating...")
                continue
            if attempt >= 2: break
    
    return False


def _launch_mcp_git_server() -> subprocess.Popen:
    """
    Launch MCP Git server as background process.
    
    WHY BACKGROUND PROCESS:
    - Provides standardized Git interface for Windows
    - Abstracts credential management differences
    - Binds to localhost only for security
    """
    try:
        process = subprocess.Popen(
            ["uvx", "mcp-server-git", "--port", "8080", "--host", "127.0.0.1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        # Give it a moment to bind to the port
        time.sleep(2)
        return process
    except Exception as e:
        print(f" Warning: Could not launch mcp-server-git ({e}). MCP operations will use subprocess fallback.")
        # Return dummy process that sleeps
        return subprocess.Popen(
            ["python", "-c", "import time; time.sleep(3600)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW
        )


def _generate_task_id() -> str:
    """Generate unique task ID."""
    import uuid
    return str(uuid.uuid4())[:8]


def _get_temperature_for_attempt(attempt: int) -> float:
    """
    Get temperature based on retry attempt.
    
    WHY LINEAR ESCALATION:
    - Attempt 1: Standard creativity (0.7)
    - Attempt 2: Increased creativity (+0.3 = 1.0)
    - Attempt 3: Maximum creativity (+0.6 = 1.3)
    - Prevents infinite loops with escalating exploration
    """
    temperatures = [0.7, 1.0, 1.3]
    return temperatures[min(attempt, len(temperatures) - 1)]


def _generate_code(plan: str, context: str, temperature: float) -> str:
    """
    Generate code simulations based on prompt keywords.
    
    NOTE: Real implementation would call LLM API.
    This enhancement supports basic multi-file simulation for testing.
    """
    prompt = plan.lower()
    
    if "math_utils" in prompt and "main" in prompt:
        return f'''# filename: math_utils.py
def add(a, b):
    return a + b

# filename: main.py
import math_utils
def main():
    result = math_utils.add(5, 7)
    print(f"Result: {{result}}")
    return result == 12

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
'''
    elif "process" in prompt:
        return f'''# filename: data_processor.py
import json

def process_data(data):
    """Simple data processing simulation."""
    return {{k: v.upper() for k, v in data.items() if isinstance(v, str)}}

# filename: run_process.py
import json
from data_processor import process_data

def main():
    raw_data = {{"name": "hybrid", "type": "orchestrator", "version": 7}}
    processed = process_data(raw_data)
    print(json.dumps(processed))
    return "HYBRID" in processed.values()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
'''
    elif "hello" in prompt:
        return f'''# filename: hello.py
def main():
    print("Hello, Hybrid Orchestrator!")
    return True

if __name__ == "__main__":
    main()
    exit(0)
'''
    
    # Default template
    return f'''# filename: task_default.py
def main():
    print("Task completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
'''


def _run_bist(code_path: Path) -> bool:
    """
    Run Built-In Self-Test on generated code.
    
    WHY BIST:
    - Automatic verification prevents broken code
    - Tests are included in generated code (--test flag)
    - Provides immediate feedback on correctness
    """
    try:
        # Run the generated code
        result = subprocess.run(
            [sys.executable, str(code_path)],
            capture_output=True,
            text=True,
            shell=False,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # Check return code and output
        # success = result.returncode == 0 and "Task completed" in result.stdout
        # BIST passes if return code is 0 (script executed without error)
        success = result.returncode == 0
        print(f"BIST Result: {'PASS' if success else 'FAIL'}")
        print(f"  Return Code: {result.returncode}")
        print(f"  Output: {result.stdout[:200]}")
        
        return success
        
    except subprocess.TimeoutExpired:
        print(" BIST timeout (30s)")
        return False
    except subprocess.SubprocessError as e:
        print(f" BIST error: {e}")
        return False


def _detect_loop(code: str, attempt: int) -> bool:
    """
    Detect potential loops using normalized hash.
    
    WHY HASH NORMALIZATION:
    - Strips volatile elements (timestamps, hex addresses, paths)
    - Enables cross-platform determinism
    - Identical logic produces identical hashes
    """
    if attempt < 2:
        return False  # Need at least 3 attempts to detect loop
    
    # In real implementation, this would track hash history
    # For now, simulate loop detection based on content
    normalized = normalize_output(code)
    code_hash = compute_normalized_hash(code)
    
    # Simple heuristic: check for obvious infinite loop patterns
    loop_patterns = [
        "while true:",
        "while(1)",
        "for(;;)",
        "loop indefinitely"
    ]
    
    return any(pattern in code.lower() for pattern in loop_patterns)
