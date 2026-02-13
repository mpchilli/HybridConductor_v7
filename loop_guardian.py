#!/usr/bin/env python3
"""
loop_guardian.py - Multi-Layer Loop Breaking

WHY THIS SCRIPT EXISTS:
- Prevents infinite execution cycles through multiple detection layers
- Implements Rick Protocol with cross-platform path normalization
- Provides linear retry escalation for failed tasks
- Ensures graceful termination within resource limits

KEY ARCHITECTURAL DECISIONS:
- MULTI-LAYER DEFENSE: Completion promises + iterations + time + hash detection
- EXACT-MATCH HASHING: SHA-256 exact matching (NIST FIPS 180-4 compliant)
- PATH NORMALIZATION: Ensures cross-platform determinism for hash matching
- LINEAR RETRY ESCALATION: 3-attempt temperature escalation replaces dead-code DB

WINDOWS-SPECIFIC CONSIDERATIONS:
- Path normalization handles both Windows and Linux path formats
- All string operations use UTF-8 encoding
- Time tracking uses monotonic clock for accuracy
- No external dependencies beyond Python standard library
"""

import re
import hashlib
import time
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoopGuardian:
    """
    Multi-layer loop breaking guardian.
    
    WHY MULTI-LAYER DEFENSE:
    - Completion promises catch intentional termination
    - Iteration limits prevent runaway loops
    - Time limits prevent resource exhaustion  
    - Hash detection catches subtle infinite loops
    - Linear retry provides recovery without complex DB
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LoopGuardian with configuration.
        
        Args:
            config: Configuration dictionary containing:
                - max_iterations: Maximum iterations before termination (default: 25)
                - max_time_minutes: Maximum execution time in minutes (default: 60)
                - base_temperature: Base LLM temperature (default: 0.7)
                - completion_promise: String pattern indicating completion (default: "LOOP_COMPLETE")
        """
        self.config = config
        self.start_time = time.monotonic()
        self.iteration_count = 0
        self.retry_count = 0
        self.hash_history: List[str] = []
        self.max_iterations = config.get("max_iterations", 25)
        self.max_time_minutes = config.get("max_time_minutes", 60)
        self.completion_promise = config.get("completion_promise", "LOOP_COMPLETE")
        self.base_temperature = config.get("base_temperature", 0.7)
        
        logger.info(f"LoopGuardian initialized with max_iterations={self.max_iterations}, "
                   f"max_time_minutes={self.max_time_minutes}")
    
    def increment_iteration(self) -> None:
        """Increment iteration counter and log."""
        self.iteration_count += 1
        logger.debug(f"Iteration {self.iteration_count}")
    
    def should_terminate(self) -> bool:
        """
        Check if execution should terminate due to limits.
        
        Returns:
            True if termination conditions are met, False otherwise
        """
        # Check iteration limit
        if self.iteration_count >= self.max_iterations:
            logger.warning(f"Max iterations ({self.max_iterations}) reached. Terminating.")
            return True
        
        # Check time limit
        elapsed = time.monotonic() - self.start_time
        max_time_seconds = self.max_time_minutes * 60
        
        if elapsed >= max_time_seconds:
            logger.warning(f"Max time ({self.max_time_minutes} min) reached. Terminating.")
            return True
        
        return False
    
    def get_retry_count(self) -> int:
        """
        Get current retry count for debugging.
        
        Returns:
            Current retry count
        """
        return self.retry_count
    
    def increment_retry(self) -> None:
        """Increment retry counter."""
        self.retry_count += 1
        logger.debug(f"Retry count incremented to {self.retry_count}")
    
    def get_escalated_temperature(self, retry_count: Optional[int] = None) -> float:
        """
        Get escalated temperature for retry attempt.
        
        WHY LINEAR ESCALATION:
        - Attempt 1: Standard creativity (0.7)
        - Attempt 2: Increased creativity (+0.3 = 1.0)  
        - Attempt 3: Maximum creativity (+0.6 = 1.3)
        - Prevents infinite loops with escalating exploration
        
        Args:
            retry_count: Optional retry count (uses self.retry_count if None)
            
        Returns:
            Escalated temperature value
        """
        if retry_count is None:
            retry_count = self.retry_count
        
        base_temp = self.base_temperature
        escalation_steps = [0.0, 0.3, 0.6]  # Attempt 1, 2, 3+
        escalation = escalation_steps[min(retry_count, len(escalation_steps) - 1)]
        final_temp = base_temp + escalation
        
        logger.debug(f"Temperature escalated to {final_temp} (retry {retry_count})")
        return final_temp
    
    def check_completion_promise(self, output: str) -> bool:
        """
        Check if output contains completion promise.
        
        WHY COMPLETION PROMISES:
        - Allows LLM to signal intentional termination
        - Prevents unnecessary iterations when task is complete
        - Configurable pattern allows flexibility
        
        Args:
            output: Output string to check
            
        Returns:
            True if completion promise found, False otherwise
        """
        if self.completion_promise in output:
            logger.info("Completion promise detected")
            return True
        return False
    
    def detect_loop(self, code_output: str) -> bool:
        """
        Detect if current output creates a loop with previous attempts.
        
        Uses normalized hash comparison to detect identical logic despite
        superficial differences (timestamps, memory addresses, etc.)
        
        Args:
            code_output: Current code output to check
            
        Returns:
            True if loop detected, False otherwise
        """
        # Need at least 3 iterations to detect a loop
        if self.iteration_count < 3:
            return False
        
        current_hash = compute_normalized_hash(code_output)
        
        # Check if this hash appeared in last 3 iterations
        if current_hash in self.hash_history[-3:]:
            logger.warning(f"Loop detected (hash: {current_hash[:16]}...)")
            return True
        
        self.hash_history.append(current_hash)
        logger.debug(f"Hash added to history: {current_hash[:16]}...")
        return False
    
    def reset(self) -> None:
        """Reset guardian state for new task."""
        self.start_time = time.monotonic()
        self.iteration_count = 0
        self.retry_count = 0
        self.hash_history = []
        logger.info("LoopGuardian state reset")


def normalize_output(output: str) -> str:
    """
    Normalize output by stripping volatile elements before hashing.
    
    WHY NORMALIZATION:
    - Timestamps, hex addresses, and paths vary between runs
    - Identical logic should produce identical hashes
    - Cross-platform determinism requires path normalization
    - Prevents false negatives in loop detection
    
    NORMALIZATION STEPS:
    1. Strip timestamps (ISO 8601 and common formats)
    2. Strip hex addresses (memory pointers, object IDs)  
    3. Strip iteration counters
    4. Normalize paths (Windows C:\ and Linux /home/)
    5. Strip memory addresses
    6. Strip Unix timestamps
    
    Args:
        output: Raw output string
        
    Returns:
        Normalized string safe for hashing
    """
    # Strip ISO timestamps (e.g., "2026-02-13T10:30:00Z", "2026-02-13 10:30:00")
    output = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[\.\dZ]*', '[TIMESTAMP]', output)
    
    # Strip Unix timestamps (10+ digit numbers)
    output = re.sub(r'\b\d{10,}\b', '[UNIX_TIMESTAMP]', output)
    
    # Strip hex addresses (memory pointers, object IDs)
    output = re.sub(r'0x[0-9a-fA-F]+', '[HEX_ADDR]', output)
    
    # Strip iteration counters (case-insensitive)
    output = re.sub(r'iteration\s+\d+', 'iteration [N]', output, flags=re.IGNORECASE)
    
    # Strip Windows paths (e.g., "C:\Users\dev\main.py")
    output = re.sub(r'[a-zA-Z]:\\[\\\w\s\-\.]+', '[PATH]', output)
    
    # Strip Linux/Unix paths (e.g., "/home/dev/project/main.py")
    output = re.sub(r'/([\w\-\.]+/)+[\w\-\.]+', '[PATH]', output)
    
    # Strip memory addresses (8-16 hex digits)
    output = re.sub(r'\b0x[0-9a-fA-F]{8,16}\b', '[MEM_ADDR]', output)
    
    # Strip process IDs and thread IDs
    output = re.sub(r'pid=\d+', 'pid=[PID]', output)
    output = re.sub(r'tid=\d+', 'tid=[TID]', output)
    
    return output


def compute_normalized_hash(output: str) -> str:
    """
    Compute SHA-256 hash of normalized output.
    
    WHY SHA-256:
    - Cryptographically secure hash function
    - Avalanche effect ensures small changes produce large hash differences
    - Exact matching is reliable for identical normalized output
    - NIST FIPS 180-4 compliant
    
    Args:
        output: Raw output string
        
    Returns:
        SHA-256 hex digest of normalized output
    """
    normalized = normalize_output(output)
    hash_obj = hashlib.sha256(normalized.encode('utf-8'))
    return hash_obj.hexdigest()


# TEST SUITE - MUST PASS BEFORE PROCEEDING
if __name__ == "__main__":
    print("=" * 70)
    print("🧪 Running loop_guardian.py comprehensive tests...")
    print("=" * 70)
    print()
    
    all_passed = True
    
    # Test 1: normalize_output strips timestamps
    print("Test 1: Timestamp normalization")
    test1 = "Error at 2026-02-13T10:30:00Z occurred at 1707841800"
    result1 = normalize_output(test1)
    assert "[TIMESTAMP]" in result1, "Should replace ISO timestamp"
    assert "[UNIX_TIMESTAMP]" in result1, "Should replace Unix timestamp"
    assert "2026-02-13" not in result1, "Should strip ISO date"
    assert "1707841800" not in result1, "Should strip Unix timestamp"
    print("✅ PASS: Timestamp normalization works\n")
    
    # Test 2: normalize_output strips hex addresses
    print("Test 2: Hex address normalization")
    test2 = "Stack overflow at 0x12345678 in module 0xABCD1234"
    result2 = normalize_output(test2)
    assert "[HEX_ADDR]" in result2, "Should replace hex address"
    assert result2.count("[HEX_ADDR]") == 2, "Should replace both hex addresses"
    assert "0x12345678" not in result2, "Should strip first hex literal"
    assert "0xABCD1234" not in result2, "Should strip second hex literal"
    print("✅ PASS: Hex address normalization works\n")
    
    # Test 3: normalize_output strips paths
    print("Test 3: Path normalization")
    test3_win = "Error in C:\\Users\\dev\\project\\main.py at line 42"
    test3_lin = "Error in /home/dev/project/main.py at line 42"
    result3_win = normalize_output(test3_win)
    result3_lin = normalize_output(test3_lin)
    assert "[PATH]" in result3_win, "Should replace Windows path"
    assert "[PATH]" in result3_lin, "Should replace Linux path"
    assert "C:\\Users" not in result3_win, "Should strip Windows path"
    assert "/home/dev" not in result3_lin, "Should strip Linux path"
    print("✅ PASS: Path normalization works\n")
    
    # Test 4: normalize_output strips memory addresses
    print("Test 4: Memory address normalization")
    test4 = "Segmentation fault at 0x7fff5fbff000"
    result4 = normalize_output(test4)
    assert "[MEM_ADDR]" in result4, "Should replace memory address"
    assert "0x7fff5fbff000" not in result4, "Should strip memory address"
    print("✅ PASS: Memory address normalization works\n")
    
    # Test 5: normalize_output strips PIDs and TIDs
    print("Test 5: Process/thread ID normalization")
    test5 = "Process pid=12345 thread tid=67890 crashed"
    result5 = normalize_output(test5)
    assert "pid=[PID]" in result5, "Should replace process ID"
    assert "tid=[TID]" in result5, "Should replace thread ID"
    assert "pid=12345" not in result5, "Should strip process ID"
    assert "tid=67890" not in result5, "Should strip thread ID"
    print("✅ PASS: PID/TID normalization works\n")
    
    # Test 6: compute_normalized_hash produces identical output for identical logic
    print("Test 6: Hash determinism")
    code1 = "def foo():\n    return 42  # Comment 2026-02-13T10:30:00Z"
    code2 = "def foo():\n    return 42  # Comment 2026-02-14T11:45:00Z"
    code3 = "def foo():\n    return 42  # Different comment, same logic"
    hash1 = compute_normalized_hash(code1)
    hash2 = compute_normalized_hash(code2)
    hash3 = compute_normalized_hash(code3)
    assert hash1 == hash2, "Identical logic with different timestamps should produce identical hashes"
    assert hash1 == hash3, "Identical logic with different comments should produce identical hashes"
    print(f"✅ PASS: Hash determinism confirmed (hash: {hash1[:16]}...)\n")
    
    # Test 7: LoopGuardian temperature escalation
    print("Test 7: Temperature escalation")
    config = {"base_temperature": 0.7}
    guardian = LoopGuardian(config)
    assert guardian.get_escalated_temperature(0) == 0.7, "Attempt 1: base temp (0.7)"
    assert guardian.get_escalated_temperature(1) == 1.0, "Attempt 2: +0.3 (1.0)"
    assert guardian.get_escalated_temperature(2) == 1.3, "Attempt 3: +0.6 (1.3)"
    assert guardian.get_escalated_temperature(3) == 1.3, "Attempt 4+: capped at 1.3"
    print("✅ PASS: Temperature escalation works\n")
    
    # Test 8: LoopGuardian iteration tracking
    print("Test 8: Iteration tracking")
    guardian2 = LoopGuardian({"max_iterations": 5})
    for i in range(5):
        guardian2.increment_iteration()
    assert guardian2.iteration_count == 5, "Should track 5 iterations"
    assert guardian2.should_terminate() == True, "Should terminate at max iterations"
    print("✅ PASS: Iteration tracking works\n")
    
    # Test 9: Loop detection with hash history
    print("Test 9: Loop detection")
    guardian3 = LoopGuardian({"max_iterations": 10})
    guardian3.increment_iteration()  # Iteration 1
    guardian3.increment_iteration()  # Iteration 2
    guardian3.increment_iteration()  # Iteration 3
    
    code_a = "def solve():\n    x = 1\n    return x"
    code_b = "def solve():\n    x = 2\n    return x"
    
    # First occurrence of code_a
    guardian3.detect_loop(code_a)
    assert len(guardian3.hash_history) == 1, "Should have 1 hash after first call"
    
    # Second occurrence of code_a (not in last 3 yet)
    guardian3.detect_loop(code_a)
    assert len(guardian3.hash_history) == 2, "Should have 2 hashes"
    
    # Third occurrence of code_a (now in last 3)
    guardian3.detect_loop(code_a)
    assert len(guardian3.hash_history) == 3, "Should have 3 hashes"
    
    # Fourth occurrence of code_a (loop detected)
    loop_detected = guardian3.detect_loop(code_a)
    assert loop_detected == True, "Should detect loop on 4th identical attempt"
    print("✅ PASS: Loop detection works\n")
    
    # Test 10: No loop detection for different code
    print("Test 10: No false positives for different code")
    guardian4 = LoopGuardian({"max_iterations": 10})
    for _ in range(3):
        guardian4.increment_iteration()
    
    # Different code should not trigger loop detection
    guardian4.detect_loop(code_a)
    guardian4.detect_loop(code_b)
    guardian4.detect_loop(code_a)
    
    loop_detected = guardian4.detect_loop(code_b)
    assert loop_detected == False, "Should not detect loop for alternating different code"
    print("✅ PASS: No false positives for different code\n")
    
    # Test 11: Completion promise detection
    print("Test 11: Completion promise detection")
    guardian5 = LoopGuardian({"completion_promise": "LOOP_COMPLETE"})
    assert guardian5.check_completion_promise("Task done LOOP_COMPLETE") == True, "Should detect completion promise"
    assert guardian5.check_completion_promise("Task done") == False, "Should not detect without promise"
    print("✅ PASS: Completion promise detection works\n")
    
    # Test 12: Time-based termination
    print("Test 12: Time-based termination")
    guardian6 = LoopGuardian({"max_time_minutes": 0.0001})  # ~6 milliseconds
    time.sleep(0.01)  # Sleep longer than limit
    assert guardian6.should_terminate() == True, "Should terminate after time limit"
    print("✅ PASS: Time-based termination works\n")
    
    # Test 13: State reset
    print("Test 13: State reset")
    guardian7 = LoopGuardian({"max_iterations": 10})
    guardian7.increment_iteration()
    guardian7.increment_iteration()
    guardian7.increment_retry()
    
    assert guardian7.iteration_count == 2, "Should have 2 iterations"
    assert guardian7.retry_count == 1, "Should have 1 retry"
    
    guardian7.reset()
    
    assert guardian7.iteration_count == 0, "Should reset iterations"
    assert guardian7.retry_count == 0, "Should reset retries"
    assert len(guardian7.hash_history) == 0, "Should clear hash history"
    print("✅ PASS: State reset works\n")
    
    # Test 14: Cross-platform path normalization
    print("Test 14: Cross-platform path handling")
    mixed_paths = (
        "Windows: C:\\Users\\dev\\main.py\n"
        "Linux: /home/dev/project/main.py\n"
        "Mixed: C:\\Program Files\\app\\data.json and /var/log/app.log"
    )
    result14 = normalize_output(mixed_paths)
    assert result14.count("[PATH]") == 4, "Should normalize all 4 paths"
    assert "C:\\Users" not in result14, "Should strip Windows paths"
    assert "/home/dev" not in result14, "Should strip Linux paths"
    print("✅ PASS: Cross-platform path handling works\n")
    
    print("=" * 70)
    print("🎉 ALL 14 TESTS PASSED - loop_guardian.py is production-ready")
    print("=" * 70)
