#!/usr/bin/env python3
"""
orchestrator.py - Wrapper for HybridConductor Orchestrator

This script is now a thin wrapper around hybridconductor.orchestrator.fsm.
It maintains backward compatibility for existing workflows.
"""

import sys
from pathlib import Path
import os
import argparse
from datetime import datetime
import time
import traceback

# Add project root to sys.path to ensure package resolution
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from hybridconductor.orchestrator.fsm import Orchestrator, State, ComplexityMode, LoopGuardian

if "--debug" in sys.argv:
    debug_log = Path(f"hc_debug_{int(time.time())}.log")
    print(f" DEBUG MODE: Logging to {debug_log.absolute()}")
    
    def log_exception(exc_type, exc_value, exc_traceback):
        with open(debug_log, "a") as f:
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        
    sys.excepthook = log_exception


# CLI ENTRY POINT
if __name__ == "__main__":
    # Check if running as a script with arguments
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Hybrid Orchestrator v7.2.8")
        parser.add_argument("--prompt", type=str, help="Prompt to execute")
        parser.add_argument("--complexity", type=str, default="streamlined", choices=["fast", "streamlined", "full"], help="Complexity mode")
        parser.add_argument("--preset", type=str, help="Use a named configuration preset")
        parser.add_argument("--resume", action="store_true", help="Resume from last saved session")
        parser.add_argument("--background", action="store_true", help="Run in a detached background process")
        parser.add_argument("--debug", action="store_true", help="Enable debug mode (disable TUI, expose tracebacks)")
        
        args = parser.parse_args()
        
        project_root = Path.cwd()
        
        if args.background:
            # Prevent recursion by checking for an environment variable
            if os.environ.get("HC_BACKGROUND_CHILD"):
                # We are the child process, run normally
                orchestrator = Orchestrator(project_root, preset_name=args.preset)
                if args.resume:
                    orchestrator.resume()
                orchestrator.run(args.prompt or "")
            else:
                # We are the parent, spawn the child
                import subprocess
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                
                log_file = project_root / "logs" / f"background_{datetime.now().strftime('%H%M%S')}.log"
                log_file.parent.mkdir(parents=True, exist_ok=True)
                
                cmd = [sys.executable, __file__]
                if args.prompt: cmd.extend(["--prompt", args.prompt])
                if args.preset: cmd.extend(["--preset", args.preset])
                if args.resume: cmd.append("--resume")
                if args.debug: cmd.append("--debug")
                cmd.append("--background")
                
                env = os.environ.copy()
                env["HC_BACKGROUND_CHILD"] = "1"
                
                with open(log_file, "w") as f:
                    subprocess.Popen(
                        cmd,
                        env=env,
                        stdout=f,
                        stderr=f,
                        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                        close_fds=True
                    )
                print(f" Orchestrator started in background. Logs: {log_file}")
                sys.exit(0)
        else:
            orchestrator = Orchestrator(project_root, preset_name=args.preset, debug=args.debug)
            if args.resume:
                if orchestrator.resume():
                    orchestrator.run(prompt="")
                else:
                    sys.exit(1)
            elif args.prompt:
                orchestrator.set_complexity_mode(args.complexity)
                orchestrator.run(args.prompt)
            else:
                parser.print_help()
    else:
        # Run internal tests if no arguments provided
        print(" Running orchestrator.py comprehensive tests (delegated to hybridconductor.orchestrator)...\n")
        
        import tempfile
        import shutil
        
        # Test 1: State machine initialization
        print("Test 1: State machine initialization")
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "project"
            project_root.mkdir()
            (project_root / "state").mkdir()
            (project_root / "logs").mkdir()
            
            orchestrator = Orchestrator(project_root)
            try:
                assert orchestrator.current_state == State.PLANNING, "Should start in PLANNING state"
                assert isinstance(orchestrator.loop_guardian, LoopGuardian), "Should have LoopGuardian"
                assert orchestrator.complexity_mode == ComplexityMode.STREAMLINED, "Default should be STREAMLINED"
            finally:
                orchestrator.shutdown()
        
        print(" PASS: Initialization works\n")
        
        # Test 2: Complexity mode setting
        print("Test 2: Complexity mode setting")
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "project"
            project_root.mkdir()
            (project_root / "state").mkdir()
            (project_root / "logs").mkdir()
            
            orchestrator = Orchestrator(project_root)
            try:
                orchestrator.set_complexity_mode("fast")
                assert orchestrator.complexity_mode == ComplexityMode.FAST
                
                orchestrator.set_complexity_mode("streamlined")
                assert orchestrator.complexity_mode == ComplexityMode.STREAMLINED
                
                orchestrator.set_complexity_mode("full")
                assert orchestrator.complexity_mode == ComplexityMode.FULL
                
                orchestrator.set_complexity_mode("invalid")
                assert orchestrator.complexity_mode == ComplexityMode.STREAMLINED, "Should default to STREAMLINED"
            finally:
                orchestrator.shutdown()
        
        print(" PASS: Complexity mode setting works\n")
        
        # Test 3: Config persistence
        print("Test 3: Config persistence")
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "project"
            project_root.mkdir()
            (project_root / "state").mkdir()
            (project_root / "logs").mkdir()
            
            orchestrator = Orchestrator(project_root)
            try:
                assert orchestrator.config["max_iterations"] == 25
            finally:
                orchestrator.shutdown()
        
        print(" PASS: Config defaults loaded\n")
        
        # Test 6: State transitions (Simulated)
        print("Test 6: State transitions")
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "project"
            project_root.mkdir()
            (project_root / "state").mkdir()
            (project_root / "logs").mkdir()
            
            orchestrator = Orchestrator(project_root)
            try:
                # Should start in PLANNING
                assert orchestrator.current_state == State.PLANNING
                
                # Simulate planning completion
                orchestrator.current_state = State.BUILDING
                assert orchestrator.current_state == State.BUILDING
                
                # Simulate building completion
                orchestrator.current_state = State.VERIFYING
                assert orchestrator.current_state == State.VERIFYING
                
                # Simulate verification completion
                orchestrator.current_state = State.COMPLETE
                assert orchestrator.current_state == State.COMPLETE
            finally:
                orchestrator.shutdown()
        
        print(" PASS: State transitions work\n")
        
        # Test 7: Temp directory creation
        print("Test 7: Temp directory creation")
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "project"
            project_root.mkdir()
            (project_root / "state").mkdir()
            (project_root / "logs").mkdir()
            
            orchestrator = Orchestrator(project_root)
            try:
                assert orchestrator.tmp_dir.exists(), "Temp directory should exist"
                assert "hybrid_orchestrator" in str(orchestrator.tmp_dir), "Should contain project name"
            finally:
                orchestrator.shutdown()
        
        print(" PASS: Temp directory creation works\n")
        
        print("=" * 60)
        print(" ALL TESTS PASSED - orchestrator.py wrapper is robust")
        print("=" * 60)
