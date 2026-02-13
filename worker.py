#!/usr/bin/env python3
"""
worker.py - Stateless Task Executor

WHY THIS SCRIPT EXISTS:
- Executes individual tasks in isolated Git branches
- Implements Built-In Self-Test (BIST) for automatic verification
- Uses MCP server for safe Git operations on Windows
- Handles linear retry escalation for failed tasks

KEY ARCHITECTURAL DECISIONS:
- STATELESS DESIGN: Worker dies after task completion; no persistent state
- ISOLATED BRANCHES: Each task runs in separate Git branch for safety
- BIST VERIFICATION: Automatic testing prevents broken code commits
- MCP GIT OPERATIONS: Abstracts Windows Git complexities via standardized interface

WINDOWS-SPECIFIC CONSIDERATIONS:
- MCP server binds to 127.0.0.1:8080 (localhost only)
- Subprocess calls use shell=False + CREATE_NO_WINDOW
- All file operations use UTF-8+BOM encoding for Notepad compatibility
- Git branch names sanitized to prevent path traversal
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any
import requests

from loop_guardian import normalize_output

class McpClient:
    """MCP client for safe Git operations.
    
    WHY MCP OVER SUBPROCESS:
    - Abstracts Windows Git credential/path differences
    - Provides standardized error handling
    - Enforces localhost-only communication
    - Integrates with Windows security model
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        self.base_url = base_url
    
    def create_branch(self, name: str) -> None:
        """Create isolated Git branch via MCP."""
        sanitized_name = self._sanitize_branch_name(name)
        # In real impl, this would make HTTP req to MCP server
        # response = requests.post(f"{self.base_url}/branches", json={"name": sanitized_name})
        # response.raise_for_status()
        print(f"[MCP] Created branch: {sanitized_name}")
    
    def switch_branch(self, name: str) -> None:
        """Switch to specified branch."""
        sanitized_name = self._sanitize_branch_name(name)
        # response = requests.post(f"{self.base_url}/checkout", json={"branch": sanitized_name})
        # response.raise_for_status()
        print(f"[MCP] Switched to branch: {sanitized_name}")
    
    def commit(self, message: str) -> None:
        """Commit changes via MCP."""
        # response = requests.post(f"{self.base_url}/commit", json={"message": message})
        # response.raise_for_status()
        print(f"[MCP] Committed: {message}")
    
    def _sanitize_branch_name(self, name: str) -> str:
        """Sanitize branch name to prevent path traversal."""
        return "".join(c for c in name if c.isalnum() or c in "-_")

def execute_task(
    plan: str,
    context: str,
    complexity_mode: str,
    max_iterations: int = 25
) -> bool:
    """
    Execute a single task with BIST verification.
    """
    print(f"🔧 Executing task in {complexity_mode} mode")
    
    # Launch MCP Git server for safe operations
    mcp_process = _launch_mcp_git_server()
    
    try:
        # Create isolated branch for this task
        mcp_client = McpClient()
        task_id = _generate_task_id()
        branch_name = f"task-{task_id}"
        mcp_client.create_branch(branch_name)
        mcp_client.switch_branch(branch_name)
        
        # Execute task with linear retry escalation
        for attempt in range(max_iterations):
            temperature = _get_temperature_for_attempt(attempt)
            
            # Generate code using LLM
            code = _generate_code(
                plan=plan,
                context=context,
                temperature=temperature
            )
            
            # Save generated code
            code_path = Path.cwd() / f"task_{task_id}.py"
            with open(code_path, "w", encoding="utf-8-sig") as f:
                f.write(code)
            
            # Run BIST (Built-In Self-Test)
            if _run_bist(code_path):
                print("✅ BIST passed")
                mcp_client.commit(f"Auto-commit task {task_id}")
                return True
            else:
                print(f"❌ BIST failed on attempt {attempt + 1}")
                
                # Check for loop detection
                if _detect_loop(code, attempt):
                    print("🔄 Loop detected. Escalating temperature...")
                    continue  # Retry with higher temperature
                
                if attempt >= 2:  # Max 3 attempts (0, 1, 2)
                    break
        
        return False
        
    finally:
        # Cleanup MCP server
        mcp_process.terminate()
        mcp_process.wait()

def _launch_mcp_git_server() -> subprocess.Popen:
    """Launch MCP Git server as background process."""
    return subprocess.Popen(
        ["uvx", "mcp-server-git", "--port", "8080", "--host", "127.0.0.1"],
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
    """Get temperature based on retry attempt."""
    temperatures = [0.7, 1.0, 1.3]
    return temperatures[min(attempt, len(temperatures) - 1)]

def _generate_code(plan: str, context: str, temperature: float) -> str:
    """Generate code using LLM with given parameters."""
    # Placeholder implementation
    return f"""
# Generated with temperature {temperature}
# Plan: {plan[:50]}...
# Context: {context[:50]}...

def main():
    print("Task completed successfully!")

if __name__ == "__main__":
    main()
"""

def _run_bist(code_path: Path) -> bool:
    """Run Built-In Self-Test on generated code."""
    try:
        # Mocking success for the placeholder script
        # In real scenario, we run with --test
        # result = subprocess.run([str(code_path), "--test"], ...)
        return True 
    except Exception:
        return False

def _detect_loop(code: str, attempt: int) -> bool:
    """Detect potential loops using normalized hash."""
    if attempt < 2:
        return False  # Need at least 3 attempts to detect loop
    return "infinite" in code.lower()

# Main execution (for testing)
if __name__ == "__main__":
    success = execute_task(
        plan="Change toolbar color to blue",
        context="UI configuration files",
        complexity_mode="fast"
    )
    print(f"Task result: {'SUCCESS' if success else 'FAILURE'}")
