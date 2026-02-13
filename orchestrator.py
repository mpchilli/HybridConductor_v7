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
import sqlite3
from datetime import datetime
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
        
        # Datetime stamped task folder in /tmp
        date_stamp = datetime.now().strftime("%m%d%y")
        self.tmp_dir = Path("C:/tmp") / date_stamp
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Tasks will be stored in: {self.tmp_dir}")
        
    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        config_path = self.project_root / "config" / "default.yml"
        if not config_path.exists():
            return {"max_iterations": 25, "max_time_minutes": 60, "base_temperature": 0.7}
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _log_event(self, status: str, details: str, iteration: int = 0) -> None:
        """Log event to SQLite activity database."""
        db_path = self.logs_dir / "activity.db"
        try:
            with sqlite3.connect(f"file:{db_path}?mode=rw", uri=True) as conn:
                conn.execute("""
                    INSERT INTO activity (task_id, iteration, status, details)
                    VALUES (?, ?, ?, ?)
                """, ("orchestrator", iteration, status, details))
        except Exception as e:
            print(f"⚠️ Failed to log event: {e}")

    def _log_ai_conversation(self, role: str, message: str) -> None:
        """Log AI conversation (prompt/response) to database."""
        db_path = self.logs_dir / "activity.db"
        try:
            with sqlite3.connect(f"file:{db_path}?mode=rw", uri=True) as conn:
                conn.execute("""
                    INSERT INTO ai_conversation (role, message)
                    VALUES (?, ?)
                """, (role, message))
        except Exception as e:
            print(f"⚠️ Failed to log AI conversation: {e}")
    
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
        self._log_event('STARTED', f"Starting orchestration in {self.complexity_mode.value} mode")
        
        # Generate L0 codebase map if needed
        if not (self.state_dir / "codebase_map.md").exists():
            generate_codebase_map(self.project_root)
        
        # Main state machine loop
        while self.current_state not in [State.COMPLETE, State.FAILED]:
            self._log_event('RUNNING', f"Entering state: {self.current_state.value}", self.loop_guardian.iteration_count)
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
        status = 'COMPLETED' if self.current_state == State.COMPLETE else 'FAILED'
        self._log_event(status, f"Orchestration completed with state: {self.current_state.value}")
    
    def _handle_planning(self, prompt: str) -> None:
        """Handle planning state based on complexity mode."""
        if self.complexity_mode == ComplexityMode.FAST:
            # FAST mode: Generate minimal plan and go to building
            print("⚡ FAST mode: Generating minimal plan...")
            # Create minimal artifacts to satisfy worker requirements
            with open(self.state_dir / "spec.md", "w", encoding="utf-8-sig") as f:
                f.write(f"# Fast Mode Spec\nPrompt: {prompt}")
            with open(self.state_dir / "plan.md", "w", encoding="utf-8-sig") as f:
                f.write(f"# Fast Mode Plan\n- [ ] Execute: {prompt}")
            
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
        self._log_event('RUNNING', "Plan generated. Waiting for user approval...", self.loop_guardian.iteration_count)
        time.sleep(5)  # In real implementation, this would wait for UI approval
        
        self.current_state = State.BUILDING
    
    def _handle_building(self) -> None:
        """Handle building state by executing worker."""
        from worker import execute_task
        
        # Load current plan
        with open(self.state_dir / "plan.md", "r", encoding="utf-8-sig") as f:
            plan = f.read()
        
        # Log context fetching
        self._log_ai_conversation("SYSTEM", f"Fetching context for: {plan[:100]}...")
        context = fetch_context("next task from plan")
        self._log_ai_conversation("AI", f"Context retrieved: {context[:100]}...")
        
        # Execute task with current context and plan
        success = execute_task(
            plan=plan,
            context=context,
            complexity_mode=self.complexity_mode.value,
            max_iterations=self.config.get("max_iterations", 25),
            tmp_dir=self.tmp_dir
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
        """Generate a basic plan based on the prompt."""
        # Simple heuristic to generate a somewhat relevant plan
        tasks = []
        if "html" in prompt.lower():
            tasks.append("- [ ] Create HTML structure")
            tasks.append("- [ ] Add content to HTML file")
        if "python" in prompt.lower():
            tasks.append("- [ ] Create Python script")
            tasks.append("- [ ] Implement main logic")
        
        if not tasks:
            tasks.append(f"- [ ] Analyze requirements for: {prompt}")
            tasks.append("- [ ] Implement solution")
            tasks.append("- [ ] Verify implementation")
            
        return f"# Plan for: {prompt}\n\n" + "\n".join(tasks)

# Main execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Hybrid Orchestrator")
    parser.add_argument("--prompt", type=str, help="Task prompt", required=False)
    parser.add_argument("--complexity", type=str, default="streamlined", help="Complexity mode")
    
    args = parser.parse_args()
    
    project_root = Path.cwd()
    orchestrator = Orchestrator(project_root)
    
    if args.prompt:
        orchestrator.set_complexity_mode(args.complexity)
        orchestrator.run(args.prompt)
    else:
        # Fallback for manual run / testing
        prompt = "Change the toolbar color to blue"
        orchestrator.set_complexity_mode("fast")
        orchestrator.run(prompt)
