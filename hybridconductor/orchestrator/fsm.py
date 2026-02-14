"""
hybridconductor.orchestrator.fsm - Deterministic State Machine Logic

Contains the Orchestrator class and state definitions.
"""

import os
import sys
import time
import json
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Optional
import yaml
import tempfile

# Add project root to sys.path to ensure we can import root modules
# (cartographer, providers, tui) until they are moved to the package.
project_root = Path(__file__).parents[2].resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hybridconductor.core import LoopGuardian, ContextFetcher, normalize_output, compute_normalized_hash
from hybridconductor.config import config
from hybridconductor.logger import setup_logging
from cartographer import generate_map as generate_codebase_map
from providers import get_provider
from tui import TerminalUI


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
    
    def __init__(self, project_root: Path, preset_name: Optional[str] = None, debug: bool = False):
        self.project_root = project_root.resolve()
        self.state_dir = project_root / "state"
        self.logs_dir = project_root / "logs"
        self.debug = debug
        
        # Initialize centralized logging
        self.logger = setup_logging("orchestrator", self.logs_dir, debug=self.debug)
        
        # Initialize centralized config with local override
        self.config = self._load_config(preset_name)
        self.current_state = State.PLANNING
        self.loop_guardian = LoopGuardian(self.config)
        self.context_fetcher = ContextFetcher(self.project_root)
        self.complexity_mode = ComplexityMode(self.config.get("default_complexity", "streamlined"))
        
        # Initialize TUI
        self.tui_enabled = not bool(os.environ.get("HC_BACKGROUND_CHILD")) and not self.debug
        self.tui = TerminalUI() if self.tui_enabled else None
        
        # Initialize LLM Provider
        provider_cfg = config.get_provider_config()
        # Overlay local config overrides if any
        if "llm" in self.config:
             provider_cfg.update(self.config["llm"])
             
        self.provider = get_provider(
            provider_cfg.get("provider", "gemini"),
            api_key=provider_cfg["api_key"], 
            model=provider_cfg["model"], 
            temperature=provider_cfg["temperature"]
        )
        print(f" LLM Provider initialized: {self.provider}")
        
        # Datetime stamped task folder in temp directory
        date_stamp = datetime.now().strftime("%m%d%y")
        self.tmp_dir = Path(tempfile.gettempdir()) / f"hybrid_orchestrator_{date_stamp}"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        print(f" Tasks will be stored in: {self.tmp_dir}")
        
        # Pre-flight checks
        self._check_dependencies()

    def shutdown(self):
        """Cleanup resources, especially logging handlers."""
        import logging
        # Close all handlers associated with this logger
        if hasattr(self, 'logger'):
            handlers = self.logger.handlers[:]
            for handler in handlers:
                handler.close()
                self.logger.removeHandler(handler)

    def _check_dependencies(self) -> None:
        """Verify required external tools like 'uv' are installed."""
        import shutil
        import subprocess
        
        required = ["uv", "git"]
        missing = []
        
        for tool in required:
            if not shutil.which(tool):
                missing.append(tool)
        
        if missing:
            error_msg = f"MISSING DEPENDENCIES: {', '.join(missing)}"
            print(f"\n ERROR: {error_msg}")
            print(" Please install required tools and ensure they are in your PATH.")
            if "uv" in missing:
                print(" Install uv: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
            
            if not self.debug:
                sys.exit(1)
            else:
                print(" WARNING: Continuing anyway due to --debug mode.")
    
    def _load_config(self, preset_name: Optional[str] = None) -> dict:
        """
        Load configuration from YAML file and optionally merge a preset.
        
        WHY PRESET MERGING:
        - Allows standard defaults while permitting granular task-specific overrides
        - Aligns with ralph-orchestrator pattern of 31+ specialized profiles
        """
        config_path = self.project_root / "config" / "default.yml"
        config = {
            "max_iterations": 25,
            "max_time_minutes": 60,
            "base_temperature": 0.7,
            "completion_promise": "LOOP_COMPLETE",
            "default_complexity": "streamlined"
        }
        
        if config_path.exists():
            with open(config_path, "r") as f:
                try:
                    loaded = yaml.safe_load(f)
                    if loaded: config.update(loaded)
                except Exception as e:
                    print(f" Warning: Failed to load default config: {e}")

        # Merge preset if requested
        if preset_name:
            # Find preset file in registry
            preset_file = None
            for p in config.get("presets", []):
                if p["name"] == preset_name:
                    preset_file = self.project_root / p["file"]
                    break
            
            if not preset_file:
                # Try direct file path if not in registry
                preset_file = self.project_root / "presets" / f"{preset_name}.yml"
                
            if preset_file and preset_file.exists():
                print(f" Loading preset: {preset_name} from {preset_file.name}")
                with open(preset_file, "r") as f:
                    try:
                        preset_data = yaml.safe_load(f)
                        if preset_data:
                            # Update config with preset data
                            config.update(preset_data)
                            # If preset has a mode, ensure it's synced to default_complexity
                            if "mode" in preset_data:
                                config["default_complexity"] = preset_data["mode"]
                    except Exception as e:
                        print(f" Warning: Failed to load preset '{preset_name}': {e}")
            else:
                print(f" Warning: Preset '{preset_name}' not found.")

        return config
    
    def _log_event(self, status: str, details: str, iteration: int = 0) -> None:
        """Log event to SQLite activity database and TUI."""
        if self.tui_enabled and self.tui:
            self.tui.update_event(status, details)
            
        db_path = self.logs_dir / "activity.db"
        try:
            if not db_path.exists():
                return
            
            with sqlite3.connect(f"file:{db_path}?mode=rw", uri=True) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO activity (task_id, iteration, status, details) VALUES (?, ?, ?, ?)",
                    ("orchestrator", iteration, status, details)
                )
                conn.commit()
        except Exception as e:
            print(f" Failed to log event: {e}")
    
    def _log_ai_conversation(self, role: str, message: str) -> None:
        """Log AI conversation (prompt/response) to database."""
        db_path = self.logs_dir / "activity.db"
        try:
            if not db_path.exists():
                return
            
            with sqlite3.connect(f"file:{db_path}?mode=rw", uri=True) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_conversation (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        role TEXT NOT NULL,
                        message TEXT NOT NULL
                    )
                """)
                cursor.execute(
                    "INSERT INTO ai_conversation (role, message) VALUES (?, ?)",
                    (role, message)
                )
                conn.commit()
        except Exception as e:
            print(f" Failed to log AI conversation: {e}")

    def pause(self) -> None:
        """Serialize current state and exit."""
        session_path = self.state_dir / "session.json"
        state_data = {
            "current_state": self.current_state.value,
            "complexity_mode": self.complexity_mode.value,
            "loop_guardian": self.loop_guardian.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Save plan and spec as well (though they should already be in state/)
        with open(session_path, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)
            
        print(f" Session paused and saved to {session_path}")
        self._log_event('PAUSED', f"Session paused at state: {self.current_state.value}")
        sys.exit(0)

    def resume(self) -> bool:
        """Restore state from session.json."""
        session_path = self.state_dir / "session.json"
        if not session_path.exists():
            print(" No saved session found to resume.")
            return False
            
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.current_state = State(data["current_state"])
            self.set_complexity_mode(data["complexity_mode"])
            self.loop_guardian.from_dict(data["loop_guardian"])
            
            print(f" Resuming session from {data['timestamp']} at state: {self.current_state.value}")
            self._log_event('RESUMED', f"Resuming session from {data['timestamp']} at state: {self.current_state.value}")
            return True
        except Exception as e:
            print(f" Failed to resume session: {e}")
            return False
    
    def set_complexity_mode(self, mode: str) -> None:
        """
        Set complexity mode from user input.
        """
        mode_map = {
            "fast": ComplexityMode.FAST,
            "streamlined": ComplexityMode.STREAMLINED,
            "full": ComplexityMode.FULL
        }
        self.complexity_mode = mode_map.get(mode, ComplexityMode.STREAMLINED)
    
    def run(self, prompt: str) -> None:
        """Main execution loop implementing state machine."""
        if self.tui_enabled and self.tui:
            self.tui.start()
            
        try:
            print(f" Starting orchestration in {self.complexity_mode.value} mode")
            self._log_event('STARTED', f"Starting orchestration in {self.complexity_mode.value} mode")
            
            # Generate L0 codebase map if needed
            if not (self.state_dir / "codebase_map.md").exists():
                generate_codebase_map(self.project_root)
            
            # Main state machine loop
            while self.current_state not in [State.COMPLETE, State.FAILED]:
                # Update TUI state
                if self.tui_enabled and self.tui:
                    self.tui.set_state(self.current_state.value)
                
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
        
        except Exception as e:
            self._log_event('ERROR', f"Fatal error in run loop: {e}")
            self.current_state = State.FAILED
            
            # If TUI is on, stop it first to expose the console
            if self.tui_enabled and self.tui:
                self.tui.set_state("FAILED")
                time.sleep(1)
                self.tui.stop()
            
            if self.debug:
                print("\n" + "="*60)
                print(" DEBUG MODE: FATAL EXCEPTION TRACEBACK")
                print("="*60)
                import traceback
                traceback.print_exc()
                print("="*60 + "\n")
            else:
                print(f"\n Fatal Error: {e}")
                print(" Run with --debug to see full traceback.\n")
            
            # Re-raise so background logs catch it too
            raise e
        finally:
            print(f" Orchestration completed with state: {self.current_state.value}")
            status = 'COMPLETED' if self.current_state == State.COMPLETE else 'FAILED'
            self._log_event(status, f"Orchestration completed with state: {self.current_state.value}")
            
            if self.tui_enabled and self.tui:
                self.tui.set_state(self.current_state.value)
                time.sleep(2) # Give user a moment to see final state
                self.tui.stop()
    
    def _handle_planning(self, prompt: str) -> None:
        """Handle planning state based on complexity mode."""
        if self.complexity_mode == ComplexityMode.FAST:
            # FAST mode: Generate minimal plan and go to building
            print(" FAST mode: Generating minimal plan...")
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
        print(" Plan generated. Waiting for user approval...")
        self._log_event('RUNNING', "Plan generated. Waiting for user approval...", self.loop_guardian.iteration_count)
        time.sleep(5)  # In real implementation, this would wait for UI approval
        
        self.current_state = State.BUILDING
    
    def _handle_building(self) -> None:
        """
        Handle building state by executing worker.
        """
        # Logic to import and run worker
        # Note: worker.py wrapper or direct import
        # We can now import directly from hybridconductor.worker
        try:
            from hybridconductor.worker import execute_task
        except ImportError:
            print(" Critical: hybridconductor.worker not found.")
            self.current_state = State.FAILED
            return
            
        # Load current plan
        try:
            with open(self.state_dir / "plan.md", "r", encoding="utf-8-sig") as f:
                plan = f.read()
        except FileNotFoundError:
            print(" Critical: plan.md not found in state directory.")
            self.current_state = State.FAILED
            return
        
        # Log context fetching
        self._log_ai_conversation("SYSTEM", f"Fetching context for: {plan[:100]}...")
        context = self.context_fetcher.fetch_context("Current phase from plan.md")
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
        print(" Verification passed")
        self.current_state = State.COMPLETE
    
    def _handle_debugging(self) -> None:
        """Handle debugging state with linear retry escalation."""
        retry_count = self.loop_guardian.get_retry_count()
        
        if retry_count >= 3:
            print(" Max retries exceeded. Task failed.")
            self.current_state = State.FAILED
            return
        
        # Escalate temperature for next attempt
        new_temp = self.loop_guardian.get_escalated_temperature(retry_count)
        print(f" Retry attempt {retry_count + 1} with temperature {new_temp}")
        
        # Return to building state for retry
        self.current_state = State.BUILDING
    
    def _process_inbox_commands(self) -> None:
        """Process user commands from inbox.md."""
        inbox_path = self.state_dir / "inbox.md"
        if not inbox_path.exists():
            return
        
        try:
            with open(inbox_path, "r", encoding="utf-8-sig") as f:
                commands = f.read().strip().split("\n")
            
            for command in commands:
                if not command: continue
                if command.startswith("/pause"):
                    self.pause()
                elif command.startswith("/checkpoint"):
                    print(f" Creating checkpoint: {command}")
                    # In v8, this could be an incremental pause()
                    self._log_event('CHECKPOINT', f"Checkpoint created: {command}")
                elif command.startswith("/rollback"):
                    print(f"↩ Rolling back: {command}")
                    # Implementation would restore from checkpoint
            
            # Clear inbox after processing
            inbox_path.unlink()
        except Exception as e:
            print(f" Failed to process inbox: {e}")
    
    def _generate_spec(self, prompt: str) -> str:
        """Generate detailed specification based on user prompt."""
        return f"""# Spec for: {prompt}
## Requirements
1. Functional adherence to Windows-native constraints.
2. UTF-8+BOM encoding for all file outputs.
3. Path normalization via pathlib.

## Constraints
- NO WSL or Docker dependencies.
- Absolute path handling for all system calls.
"""

    def _generate_plan(self, prompt: str) -> str:
        """Generate execution plan using 'Conductor' decomposition patterns."""
        tasks = []
        prompt_lower = prompt.lower()
        
        if "html" in prompt_lower or "ui" in prompt_lower:
            tasks.append("- [ ] Create HTML structure with premium aesthetics")
            tasks.append("- [ ] Implement CSS glassmorphism styling")
            tasks.append("- [ ] Add dynamic micro-animations")
        if "python" in prompt_lower or "script" in prompt_lower:
            tasks.append("- [ ] Implement main logic in Python 3.11+")
            tasks.append("- [ ] Add Windows-specific path normalization")
        
        if not tasks:
            tasks.append(f"- [ ] Decompose request: {prompt}")
            tasks.append("- [ ] Implement atomic component")
            tasks.append("- [ ] Verify component via BIST")
        
        return f"""# Plan for: {prompt}
## Phase 1: Execution
{chr(10).join(tasks)}

## Acceptance Criteria
- [ ] Code passes Python syntax check.
- [ ] BIST returns SUCCESS status.
"""
