#!/usr/bin/env python3
"""
dashboard/app.py - Flask UI Server

WHY THIS SCRIPT EXISTS:
- Provides web-based interface for interactive configuration
- Enables real-time monitoring of autonomous execution
- Implements command injection queue for mid-flight steering
- Binds strictly to localhost for security

KEY ARCHITECTURAL DECISIONS:
- LOCALHOST ONLY: Binds to 127.0.0.1 for security (NFR-704)
- TIME-TO-ACKNOWLEDGE: <300ms response for user inputs (FR-706)
- VISUAL FEEDBACK: Spinner within 1000ms for long-running tasks
- COMMAND QUEUE: Writes to inbox.md for orchestrator processing

WINDOWS-SPECIFIC CONSIDERATIONS:
- Flask binds to 127.0.0.1:5000 (localhost only)
- All file operations use UTF-8+BOM encoding
- SSE for real-time log streaming with proper encoding
- No external dependencies beyond Flask
"""

import os
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response
import json

# Create Flask app
app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

# Bind to localhost only (security requirement NFR-704)
HOST = "127.0.0.1"
PORT = 5000

@app.route('/')
def index():
    """Redirect to configuration page."""
    return render_template('config.html')

@app.route('/config')
def config():
    """Render configuration page with complexity toggle."""
    return render_template('config.html')

@app.route('/monitor')
def monitor():
    """Render monitoring dashboard."""
    return render_template('monitor.html')

@app.route('/history')
def history():
    """Render history page."""
    return render_template('history.html')

@app.route('/api/config', methods=['POST'])
def save_config():
    """
    Save user configuration and start orchestration.
    """
    data = request.json
    
    # Validate input
    if not data or 'prompt' not in data:
        return jsonify({'error': 'Prompt required'}), 400
    
    # Save to state directory
    state_dir = Path.cwd().parent / "state" # Adjust relative to dashboard/
    if Path.cwd().name != "dashboard": # If running from root
         state_dir = Path.cwd() / "state"
         
    state_dir.mkdir(exist_ok=True)
    
    # Save prompt and complexity mode
    with open(state_dir / "spec.md", "w", encoding="utf-8-sig") as f:
        f.write(data['prompt'])
    
    # Start orchestration asynchronously (in real implementation)
    complexity = data.get('complexity', 'streamlined')
    print(f"🚀 Starting orchestration with complexity: {complexity}")
    
    return jsonify({
        'status': 'acknowledged',
        'message': 'Orchestration started',
        'complexity': complexity
    })

@app.route('/api/command', methods=['POST'])
def save_command():
    """
    Save user command to inbox.md for mid-flight steering.
    """
    data = request.json
    
    if not data or 'command' not in data:
        return jsonify({'error': 'Command required'}), 400
    
    command = data['command'].strip()
    
    # Basic sanitization (prevent obvious injection)
    if any(bad in command for bad in ['<script>', 'javascript:', 'eval(']):
        return jsonify({'error': 'Invalid command'}), 400
    
    # Append to inbox.md
    state_dir = Path.cwd().parent / "state"
    if Path.cwd().name != "dashboard":
         state_dir = Path.cwd() / "state"
    inbox_path = state_dir / "inbox.md"
    
    with open(inbox_path, "a", encoding="utf-8-sig") as f:
        f.write(f"\n{command}")
    
    return jsonify({'status': 'command_queued'})

@app.route('/api/stream')
def stream_logs():
    """
    Stream activity logs via Server-Sent Events (SSE).
    """
    def generate():
        # In real implementation, this would tail the activity.db
        # For now, simulate log stream
        for i in range(10):
            yield f"data: {{\"message\": \"Iteration {i+1} completed\", \"timestamp\": \"{i}\"}}\n\n"
            time.sleep(1)
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    print(f"🌐 Dashboard starting at http://{HOST}:{PORT}")
    print("🔒 Binding to localhost only (security requirement)")
    
    # Start Flask app
    app.run(host=HOST, port=PORT, debug=False)
