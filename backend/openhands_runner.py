import subprocess
import sys
import shutil
import os
from pathlib import Path
from typing import Optional

class OpenHandsRunner:
    """
    Wrapper for running OpenHands in dockerless mode using the 'process' runtime.
    """
    
    def __init__(self):
        self.uv_path = shutil.which("uv")
        self.python_path = sys.executable

    def check_prerequisites(self) -> dict:
        """Check if 'uv' is installed and accessible."""
        return {
            "uv_installed": bool(self.uv_path),
            "python_version": sys.version.split()[0]
        }

    def install_openhands(self) -> bool:
        """Attempt to install OpenHands via uv tool."""
        if not self.uv_path:
            print("ERROR: 'uv' tool not found. Please install it first: https://docs.astral.sh/uv/")
            return False
            
        try:
            print("Installing/Updating OpenHands via uv...")
            # Using --force to ensure we get a clean install if needed, though usually just 'install' is fine
            subprocess.run([self.uv_path, "tool", "install", "openhands", "--python", "3.12"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to install OpenHands: {e}")
            return False

    def start_server(self, port: int = 3000) -> None:
        """
        Start the OpenHands server in process mode.
        This is a blocking call.
        """
        if not self.uv_path:
            raise RuntimeError("'uv' is required to run OpenHands.")

        cmd = ["openhands", "serve", "--runtime=process", f"--port={port}"]
        
        print(f"Starting OpenHands server on port {port} (Runtime: process)...")
        print("Disclaimer: Process mode runs outside Docker. Use with caution.")
        
        try:
            # We explicitly don't use shell=True to avoid injection, but we rely on 'openhands' being on PATH after uv install
            # If path isn't updated immediately, might need partial reload or full path
            # uv tools usually link to a known bin location. 
            
            # Allow user to interrupt
            subprocess.run(cmd, check=True)
        except FileNotFoundError:
             print("ERROR: 'openhands' command not found. Did the installation succeed?")
        except KeyboardInterrupt:
            print("\nOpenHands server stopped by user.")
        except Exception as e:
            print(f"ERROR: Unexpected error running OpenHands: {e}")

if __name__ == "__main__":
    runner = OpenHandsRunner()
    checks = runner.check_prerequisites()
    if not checks["uv_installed"]:
        print("Prerequisite check user failed: 'uv' not installed.")
        sys.exit(1)
        
    # Optional auto-install
    # if runner.install_openhands():
    #    runner.start_server()
    print("OpenHandsRunner ready. Import this class to use.")
