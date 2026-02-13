#!/usr/bin/env python3
import webview
import sys
import threading
import time
import socket
import subprocess
import os
from pathlib import Path

# Configuration
HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}/"
DASHBOARD_SCRIPT = Path("backend/dashboard/app.py")

def is_port_open(host, port):
    """Check if the port is open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def start_backend():
    """Starts the Flask backend as a subprocess."""
    print(f"🚀 Starting Backend on {URL}...")
    
    # Check if already running
    if is_port_open(HOST, PORT):
        print(f"⚠️ Port {PORT} is already in use. Assuming Dashboard is running.")
        return None

    cmd = [sys.executable, str(DASHBOARD_SCRIPT)]
    
    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(Path.cwd()),
            env=os.environ.copy()
        )
        return process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def wait_for_server():
    """Waits for the server to be ready."""
    print("⏳ Waiting for server to be ready...")
    attempts = 0
    while not is_port_open(HOST, PORT):
        time.sleep(0.5)
        attempts += 1
        if attempts > 30:
            print("❌ Server timeout.")
            return False
    print("✅ Server is ready!")
    return True

def on_closed():
    """Callback when window is closed."""
    print("🛑 Window closed. Shutting down...")
    os._exit(0)

def main():
    print("🖥️ Initializing HybridConductor GUI...")
    
    # 1. Start Backend
    backend_process = start_backend()
    
    # 2. Wait for Server
    if not wait_for_server():
        print("❌ Could not connect to backend. Exiting.")
        if backend_process:
            backend_process.terminate()
        sys.exit(1)

    # 3. Create Window
    print("🎨 Creating window...")
    window = webview.create_window(
        "HybridConductor v8.0", 
        URL,
        width=1280,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )
    
    # 4. Start GUI Loop
    webview.start(on_closed, debug=True)

    # 5. Cleanup
    if backend_process:
        print("👋 Terminating backend...")
        backend_process.terminate()

if __name__ == "__main__":
    main()
