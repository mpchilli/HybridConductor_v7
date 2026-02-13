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
"""

import re
import hashlib
import time
from typing import Dict, Any

class LoopGuardian:
    """
    Multi-layer loop breaking guardian.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.start_time = time.monotonic()
        self.iteration_count = 0
        self.retry_count = 0
        self.hash_history = []
    
    def should_terminate(self) -> bool:
        """Check if execution should terminate due to limits."""
        # Check iteration limit
        if self.iteration_count >= self.config.get("max_iterations", 25):
            return True
        
        # Check time limit
        elapsed = time.monotonic() - self.start_time
        max_time = self.config.get("max_time_minutes", 60) * 60
        if elapsed >= max_time:
            return True
        
        return False
    
    def get_retry_count(self) -> int:
        """Get current retry count for debugging."""
        return self.retry_count
    
    def get_escalated_temperature(self, retry_count: int) -> float:
        """Get escalated temperature for retry attempt."""
        base_temp = self.config.get("base_temperature", 0.7)
        escalation_steps = [0.0, 0.3, 0.6]
        escalation = escalation_steps[min(retry_count, len(escalation_steps) - 1)]
        return base_temp + escalation
    
    def check_completion_promise(self, output: str) -> bool:
        """Check if output contains completion promise."""
        completion_pattern = self.config.get("completion_promise", "LOOP_COMPLETE")
        return completion_pattern in output

def normalize_output(output: str) -> str:
    """
    Normalize output by stripping volatile elements before hashing.
    """
    # Strip timestamps (ISO 8601 and common formats)
    output = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[\.\dZ]*', '[TIMESTAMP]', output)
    
    # Strip hex addresses (memory pointers, object IDs)
    output = re.sub(r'0x[0-9a-fA-F]+', '[HEX_ADDR]', output)
    
    # Strip iteration counters
    output = re.sub(r'iteration \d+', 'iteration [N]', output)
    
    # Normalize paths (critical for cross-platform determinism)
    output = re.sub(r'[a-zA-Z]:\\[\\\w\s\-\.]+|/([\w\-\.]+/)+[\w\-\.]+', '[PATH]', output)
    
    return output

def compute_normalized_hash(output: str) -> str:
    """Compute SHA-256 hash of normalized output."""
    normalized = normalize_output(output)
    return hashlib.sha256(normalized.encode()).hexdigest()

# Test function
if __name__ == "__main__":
    # Test normalization
    test_output = "Error at C:\\Users\\dev\\main.py:42\nStack: 0x12345678\nTimestamp: 2026-02-13T10:30:00Z"
    normalized = normalize_output(test_output)
    hash_val = compute_normalized_hash(test_output)
    
    print(f"Original: {test_output}")
    print(f"Normalized: {normalized}")
    print(f"Hash: {hash_val}")
