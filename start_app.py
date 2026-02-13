#!/usr/bin/env python3
import subprocess
import sys
import time
import webbrowser
import socket
from pathlib import Path

# Configuration
DASHBOARD_SCRIPT = Path("dashboard/app.py")
HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}/monitor"

def is_port_open(host, port):
    """Check if the port is open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def main():
    print("🚀 Initializing Hybrid Orchestrator System...")
    print(f"🐍 Python Executable: {sys.executable}")
    print(f"📂 Current Working Directory: {Path.cwd()}")
    
    # 1. Start Dashboard Server
    print(f"📡 Launching Dashboard on {HOST}:{PORT}...")
    
    cmd = [sys.executable, str(DASHBOARD_SCRIPT)]
    
    try:
        # Start process
        # We redirect stderr to stdout to see errors in the console
        process = subprocess.Popen(
            cmd,
            cwd=str(Path.cwd()),
            # stdout=subprocess.DEVNULL, # Commented out for debugging
            # stderr=subprocess.DEVNULL  # Commented out for debugging
        )
        
        # 2. Wait for Server Ready
        print("⏳ Waiting for server to start...")
        attempts = 0
        while not is_port_open(HOST, PORT):
            time.sleep(0.5)
            attempts += 1
            if attempts > 20: 
                print("❌ Server timeout.")
                process.terminate()
                sys.exit(1)
            
            if process.poll() is not None:
                print("❌ Server exited unexpectedly.")
                sys.exit(1)
                
        print("✅ Server is ready!")
        
        # 3. Open Browser
        print(f"🌐 Opening browser to {URL}")
        webbrowser.open(URL)
        
        print("\n✨ System Running! Press Ctrl+C to stop.")
        
        # 4. Keep Alive
        while True:
            time.sleep(1)
            if process.poll() is not None:
                print("⚠️ Server stopped.")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping system...")
    finally:
        if 'process' in locals():
            process.terminate()
            process.wait()
            print("👋 distinct shutdown complete.")

if __name__ == "__main__":
    main()
