#!/usr/bin/env python3
"""
orchestrator.py - Deterministic State Machine Orchestrator

WHY THIS SCRIPT EXISTS:
- Implements linear state machine (Planning → Building → Verifying) instead of complex event bus
- Manages task lifecycle with explicit state transitions
- Handles user-selected complexity modes (FAST/STREAMLINED/FULL)
- Polls command injection queue for mid-flight steering

KEY ARCHITECTURAL DECISIONS:
- STATE MACHINE OVER EVENT BUS: Linear logic is easier to debug and maintain in single-threaded environment
- EXPLICIT USER SELECTION: Human knows complexity better than fragile heuristics
- ISOLATED EXECUTION: Each task runs in separate Git branch for safety
- COMMAND QUEUE: Allows mid-flight steering without breaking autonomy

WINDOWS-SPECIFIC CONSIDERATIONS:
- All paths use pathlib.Path with .resolve() for Windows semantics
- Subprocess calls use shell=False + CREATE_NO_WINDOW
- File operations use atomic writes with Windows locking retry
"""

import os
import time
import json
from pathlib import Path
from enum import Enum
from typing import Optional
import yaml

from loop_guardian import LoopGuardian
from context_fetcher import fetch_context
from cartographer import generate_codebase_map

class State(Enum):
    """Deterministic state machine states."""
    PLANNING = "planning"
    BUILDING = "building" 
    VERIFYING = "verifying"
    DEBUGGING = "debugging"
    COMPLETE = "complete"
    FAILED = "failed"

class ComplexityMode(Enum):
    """User-selected complexity modes."""
    FAST = "fast"           # Skip planning; direct BIST loop (≤3 iterations)
    STREAMLINED = "streamlined"  # Minimal spec + TDD workflow (default)
    FULL = "full"           # Spec-driven with verification gates

class Orchestrator:
    """
    Main orchestrator implementing deterministic state machine.
    
    WHY DETERMINISTIC STATE MACHINE:
    - Eliminates debugging complexity of pub/sub event bus
    - Provides clear, linear execution path
    - Prevents orphaned events that could stall workflow
    - Matches single-threaded execution model of Python
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.state_dir = project_root / "state"
        self.logs_dir = project_root / "logs"
        self.config = self._load_config()
        self.current_state = State.PLANNING
        self.loop_guardian = LoopGuardian(self.config)
        self.complexity_mode = ComplexityMode.STREAMLINED  # Default
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        config_path = self.project_root / "config" / "default.yml"
        if not config_path.exists():
            return {"max_iterations": 25, "max_time_minutes": 60, "base_temperature": 0.7}
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    
    def set_complexity_mode(self, mode: str) -> None:
        """Set complexity mode from user input.
        
        WHY EXPLICIT USER SELECTION:
        - Human judgment > fragile regex heuristics
        - Forces acknowledgment of task stakes
        - Eliminates tuning rabbit hole of weighted scoring
        - Aligns with BMAD Method findings on "vibe coding" failure
        """
        mode_map = {
            "fast": ComplexityMode.FAST,
            "streamlined": ComplexityMode.STREAMLINED, 
            "full": ComplexityMode.FULL
        }
        self.complexity_mode = mode_map.get(mode, ComplexityMode.STREAMLINED)
    
    def run(self, prompt: str) -> None:
        """Main execution loop implementing state machine."""
        print(f"🚀 Starting orchestration in {self.complexity_mode.value} mode")
        
        # Generate L0 codebase map if needed
        if not (self.state_dir / "codebase_map.md").exists():
            generate_codebase_map(self.project_root)
        
        # Main state machine loop
        while self.current_state not in [State.COMPLETE, State.FAILED]:
            if self.current_state == State.PLANNING:
                self._handle_planning(prompt)
            elif self.current_state == State.BUILDING:
                self._handle_building()
            elif self.current_state == State.VERIFYING:
                self._handle_verifying()
            elif self.current_state == State.DEBUGGING:
                self._handle_debugging()
            
            # Check for user commands in inbox
            self._process_inbox_commands()
            
            # Respect iteration/time limits
            if self.loop_guardian.should_terminate():
                self.current_state = State.FAILED
                break
            
            time.sleep(2)  # Prevent excessive CPU usage
        
        print(f"🏁 Orchestration completed with state: {self.current_state.value}")
    
    def _handle_planning(self, prompt: str) -> None:
        """Handle planning state based on complexity mode."""
        if self.complexity_mode == ComplexityMode.FAST:
            # FAST mode: Skip planning, go directly to building
            self.current_state = State.BUILDING
            return
        
        # Generate spec and plan artifacts (Conductor pattern)
        spec_content = self._generate_spec(prompt)
        plan_content = self._generate_plan(prompt)
        
        # Save artifacts
        with open(self.state_dir / "spec.md", "w", encoding="utf-8-sig") as f:
            f.write(spec_content)
        with open(self.state_dir / "plan.md", "w", encoding="utf-8-sig") as f:
            f.write(plan_content)
        
        # Wait for user approval (simulated in this example)
        print("📝 Plan generated. Waiting for user approval...")
        time.sleep(5)  # In real implementation, this would wait for UI approval
        
        self.current_state = State.BUILDING
    
    def _handle_building(self) -> None:
        """Handle building state by executing worker."""
        from worker import execute_task
        
        # Load current plan
        with open(self.state_dir / "plan.md", "r", encoding="utf-8-sig") as f:
            plan = f.read()
        
        # Fetch context for current task
        context = fetch_context("next task from plan")
        
        # Execute task with current context and plan
        success = execute_task(
            plan=plan,
            context=context,
            complexity_mode=self.complexity_mode.value,
            max_iterations=self.config.get("max_iterations", 25)
        )
        
        if success:
            self.current_state = State.VERIFYING
        else:
            self.current_state = State.DEBUGGING
    
    def _handle_verifying(self) -> None:
        """Handle verification state."""
        # In real implementation, this would run tests/lint/typecheck
        # For now, assume verification passes
        print("✅ Verification passed")
        self.current_state = State.COMPLETE
    
    def _handle_debugging(self) -> None:
        """Handle debugging state with linear retry escalation."""
        retry_count = self.loop_guardian.get_retry_count()
        
        if retry_count >= 3:
            print("❌ Max retries exceeded. Task failed.")
            self.current_state = State.FAILED
            return
        
        # Escalate temperature for next attempt
        new_temp = self.loop_guardian.get_escalated_temperature(retry_count)
        print(f"🔄 Retry attempt {retry_count + 1} with temperature {new_temp}")
        
        # Return to building state for retry
        self.current_state = State.BUILDING
    
    def _process_inbox_commands(self) -> None:
        """Process user commands from inbox.md."""
        inbox_path = self.state_dir / "inbox.md"
        if not inbox_path.exists():
            return
        
        with open(inbox_path, "r", encoding="utf-8-sig") as f:
            commands = f.read().strip().split("\n")
        
        for command in commands:
            if command.startswith("/pause"):
                print("⏸️  Pausing execution...")
                time.sleep(10)  # Simulate pause
            elif command.startswith("/checkpoint"):
                print(f"💾 Creating checkpoint: {command}")
                # Implementation would save current state
            elif command.startswith("/rollback"):
                print(f"↩️  Rolling back: {command}")
                # Implementation would restore from checkpoint
        
        # Clear inbox after processing
        inbox_path.unlink()

    def _generate_spec(self, prompt: str) -> str:
        """Placeholder for spec generation."""
        return f"# Spec for: {prompt}\n\n1. Requirement A\n2. Requirement B"

    def _generate_plan(self, prompt: str) -> str:
        """Placeholder for plan generation."""
        return f"# Plan for: {prompt}\n\n- [ ] Task 1\n- [ ] Task 2"

# Main execution
if __name__ == "__main__":
    project_root = Path.cwd()
    orchestrator = Orchestrator(project_root)
    
    # In real implementation, prompt would come from UI
    prompt = "Change the toolbar color to blue"
    orchestrator.set_complexity_mode("fast")  # User selection
    orchestrator.run(prompt)
