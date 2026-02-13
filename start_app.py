#!/usr/bin/env python3
import subprocess
import sys
import time
import webbrowser
import socket
import os
import shutil
from pathlib import Path

# Configuration
# Path relative to the root of the project
DASHBOARD_SCRIPT = Path("backend/dashboard/app.py")
BACKEND_DIR = Path("backend")
STATIC_DIR = BACKEND_DIR / "static"
HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}/"

def is_port_open(host, port):
    """Check if the port is open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def check_frontend_build():
    """Checks if frontend build exists, otherwise builds it."""
    index_file = STATIC_DIR / "index.html"
    
    if not index_file.exists():
        print("⚠️ Frontend build not found. Initialization required!")
        print("📦 Installing and building frontend... (This may take a minute)")
        
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        
        try:
            # Check if npm is installed
            if not shutil.which("npm"):
                 print("❌ Error: Node.js/npm is not installed or not in PATH.")
                 print("   Please install Node.js to use the dashboard.")
                 sys.exit(1)

            # 1. Install Dependencies
            print("   Running 'npm install'...")
            subprocess.run([npm_cmd, "install"], cwd=str(BACKEND_DIR), check=True, shell=True)
            
            # 2. Build Frontend
            print("   Running 'npm run build'...")
            subprocess.run([npm_cmd, "run", "build"], cwd=str(BACKEND_DIR), check=True, shell=True)
            
            print("✅ Frontend built successfully!")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build frontend: {e}")
            sys.exit(1)
    else:
        print("✅ Frontend build found.")

def main():
    print("🚀 Initializing Hybrid Orchestrator System...")
    print(f"🐍 Python Executable: {sys.executable}")
    print(f"📂 Current Working Directory: {Path.cwd()}")
    
    # 0. Check/Build Frontend
    check_frontend_build()
    
    # 1. Start Dashboard Server
    print(f"📡 Launching Dashboard on {HOST}:{PORT}...")
    
    if is_port_open(HOST, PORT):
        print(f"⚠️ Port {PORT} is already in use. Assuming Dashboard is running.")
        print(f"🌐 Opening browser to {URL}")
        webbrowser.open(URL)
        return

    cmd = [sys.executable, str(DASHBOARD_SCRIPT)]
    
    try:
        # Start process
        process = subprocess.Popen(
            cmd,
            cwd=str(Path.cwd()),
            # stdout=subprocess.DEVNULL, 
            # stderr=subprocess.DEVNULL 
        )
        
        # 2. Wait for Server Ready
        print("⏳ Waiting for server to start...")
        attempts = 0
        while not is_port_open(HOST, PORT):
            time.sleep(0.5)
            attempts += 1
            if attempts > 20: 
                print("❌ Server timeout. Check logs.")
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
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            process.wait()
            print("👋 distinct shutdown complete.")

if __name__ == "__main__":
    main()
