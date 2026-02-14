#!/usr/bin/env python3
"""
worker.py - Wrapper for HybridConductor Worker

This script is now a thin wrapper around hybridconductor.worker.task_runner.
It maintains backward compatibility for existing workflows.
"""

import sys
from pathlib import Path

# Add project root to sys.path to ensure package resolution
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hybridconductor.worker import execute_task
from hybridconductor.worker.task_runner import (
    _run_bist,
    _generate_task_id,
    _get_temperature_for_attempt,
    _generate_code,
    _detect_loop,
    log_ai_conversation
)
from hybridconductor.mcp.client import McpClient
from hybridconductor.utils.safe_cleanup import safe_tempdir
import sqlite3
import os

if __name__ == "__main__":
    # If run directly as a script without arguments, run the BIST suite
    # This matches the original behavior where `python worker.py` ran tests
    
    print(" Running worker.py comprehensive tests (delegated to hybridconductor.worker)...\n")
    
    import tempfile
    
    # Test 1: Branch name sanitization
    print("Test 1: Branch name sanitization")
    client = McpClient()
    test_cases = [
        ("valid-branch", "valid-branch"),
        ("../../etc/passwd", "etcpasswd"),
        ("branch with spaces", "branchwithspaces"),
        ("special!@#$%^&*()", "special"),
        ("a" * 100, "a" * 50),  # Should truncate
    ]
    
    for input_name, expected in test_cases:
        result = client._sanitize_branch_name(input_name)
        assert result == expected, f"Expected '{expected}', got '{result}'"
    
    print(" PASS: Branch sanitization works\n")
    
    # Test 2: Temperature escalation
    print("Test 2: Temperature escalation")
    assert _get_temperature_for_attempt(0) == 0.7, "Attempt 1: 0.7"
    assert _get_temperature_for_attempt(1) == 1.0, "Attempt 2: 1.0"
    assert _get_temperature_for_attempt(2) == 1.3, "Attempt 3: 1.3"
    assert _get_temperature_for_attempt(3) == 1.3, "Attempt 4+: capped at 1.3"
    print(" PASS: Temperature escalation works\n")
    
    # Test 3: Code generation produces multi-file format
    print("Test 3: Code generation produces multi-file format")
    code = _generate_code("Test plan", "Test context", 0.7)
    assert code.startswith("# filename: "), "Should start with filename header"
    assert "def main():" in code, "Should contain main function"
    print(" PASS: Code generation works\n")
    
    # Test 4: BIST execution
    print("Test 4: BIST execution")
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test_task.py"
        test_code = '''#!/usr/bin/env python3
def main():
    print("Task completed successfully!")
    return True
if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
'''
        test_file.write_text(test_code, encoding="utf-8")
        
        # Make executable on Windows
        result = _run_bist(test_file)
        assert result == True, "BIST should pass for valid code"
    
    print(" PASS: BIST execution works\n")
    
    # Test 5: Loop detection
    print("Test 5: Loop detection")
    infinite_loop_code = """
while True:
    print("looping")
"""
    normal_code = """
def main():
    return True
"""
    
    assert _detect_loop(infinite_loop_code, 2) == True, "Should detect infinite loop"
    assert _detect_loop(normal_code, 2) == False, "Should not detect normal code as loop"
    assert _detect_loop(normal_code, 0) == False, "Should not check on attempt 0"
    
    print(" PASS: Loop detection works\n")
    
    # Test 6: Task ID generation
    print("Test 6: Task ID generation")
    task_id1 = _generate_task_id()
    task_id2 = _generate_task_id()
    assert isinstance(task_id1, str), "Should return string"
    assert len(task_id1) == 8, "Should be 8 characters"
    assert task_id1 != task_id2, "Should generate unique IDs"
    print(" PASS: Task ID generation works\n")
    
    # Test 7: AI conversation logging
    print("Test 7: AI conversation logging")
    
    # Use localized directory and environment for logging test
    with safe_tempdir(prefix="hc_test_log_") as tmp_path:
        test_root = tmp_path
        (test_root / "logs").mkdir()
        
        # We need to temporarily change CWD because log_ai_conversation 
        # uses Path("logs") relative to CWD if not passed db_path (or we pass it explicitly)
        # In current task_runner, it expects explicit db_path or defaults to logs/activity.db
        
        old_cwd = os.getcwd()
        os.chdir(str(test_root))
        
        try:
            test_db = Path("logs") / "activity.db"
            
            # Create test database
            conn = sqlite3.connect(f"file:{test_db}?mode=rwc", uri=True)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_conversation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """)
            conn.commit()
            conn.close()
            
            # Test logging
            log_ai_conversation("TEST", "Test message", test_db)
            
            # Verify it was logged
            conn = sqlite3.connect(f"file:{test_db}?mode=rw", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM ai_conversation WHERE role='TEST'")
            count = cursor.fetchone()[0]
            conn.close()
            
            assert count > 0, "Should log conversation"
            print(" logging validated in temp environment")
        finally:
            os.chdir(old_cwd)
    
    print(" PASS: AI conversation logging works\n")
    
    print("=" * 60)
    print(" ALL 7 TESTS PASSED - worker.py wrapper is functional")
    print("=" * 60)
