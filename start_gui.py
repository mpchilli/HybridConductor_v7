#!/usr/bin/env python3
import webview
import sys
import threading
import time
import os
from backend.dashboard.app import app

# Configuration
HOST = "127.0.0.1"
PORT = 5000
URL = f"http://{HOST}:{PORT}/"

def start_backend():
    """Starts the Flask backend in a separate thread."""
    print(f"🚀 Starting Backend on {URL}...")
    
    # Run the Flask app
    # use_reloader=False is crucial for Pywebview + Threading
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)

def on_closed():
    """Callback when window is closed."""
    print("🛑 Window closed. Shutting down...")
    os._exit(0)

def main():
    print("🖥️ Initializing HybridConductor GUI...")
    
    # 1. Start Backend Thread
    t = threading.Thread(target=start_backend, daemon=True)
    t.start()

    # 2. Wait for Server (Simple delay ensures thread starts)
    # Since it's in-process, we trust it spins up quickly.
    # A robust check could ping the port, but this is usually sufficient for local GUI.
    time.sleep(1) 

    # 3. Create Window
    print("🎨 Creating window...")
    webview.create_window(
        "HybridConductor v8.0", 
        URL,
        width=1280,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )
    
    # 4. Start GUI Loop
    webview.start(on_closed, debug=True)

if __name__ == "__main__":
    main()
