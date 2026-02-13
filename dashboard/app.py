import os
import time
import sqlite3
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response

# Create Flask app
app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

# Bind to localhost only (security requirement NFR-704)
HOST = "127.0.0.1"
PORT = 5000

@app.route('/')
def index():
    """Redirect to monitoring page."""
    return render_template('monitor.html')

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

@app.route('/process')
def process_flow():
    """Render process flow visualization."""
    return render_template('process_flow.html')

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
    
    # Start orchestration asynchronously
    complexity = data.get('complexity', 'streamlined')
    prompt = data['prompt']
    
    print(f"🚀 Starting orchestration with complexity: {complexity}")
    
    # Spawn orchestrator process
    try:
        # Use python from current environment
        import sys
        import subprocess
        
        cmd = [sys.executable, "orchestrator.py", "--prompt", prompt, "--complexity", complexity]
        
        # Run in separate process, detached if possible or just Popen
        # We need to set cwd to project root
        project_root = Path.cwd().parent if Path.cwd().name == "dashboard" else Path.cwd()
        
        subprocess.Popen(
            cmd,
            cwd=str(project_root),
            creationflags=subprocess.CREATE_NEW_CONSOLE # Open in new window for visibility
        )
        
        return jsonify({
            'status': 'started',
            'message': 'Orchestration process started',
            'complexity': complexity
        })
    except Exception as e:
        print(f"❌ Failed to start orchestrator: {e}")
        return jsonify({'error': str(e)}), 500

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
        last_id = 0
        db_path = Path.cwd().parent / "logs" / "activity.db"
        if Path.cwd().name != "dashboard":
             db_path = Path.cwd() / "logs" / "activity.db"

        while True:
            try:
                if db_path.exists():
                    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT id, timestamp, status, details FROM activity WHERE id > ? ORDER BY id ASC", (last_id,))
                        rows = cursor.fetchall()
                        
                        for row in rows:
                            last_id = row[0]
                            data = {
                                "timestamp": row[1],
                                "status": row[2],
                                "message": row[3]
                            }
                            yield f"data: {json.dumps(data)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            time.sleep(1)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/stream_ai')
def stream_ai_logs():
    """
    Stream AI conversation via Server-Sent Events (SSE).
    """
    def generate():
        last_id = 0
        db_path = Path.cwd().parent / "logs" / "activity.db"
        if Path.cwd().name != "dashboard":
             db_path = Path.cwd() / "logs" / "activity.db"

        while True:
            try:
                if db_path.exists():
                    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT id, timestamp, role, message FROM ai_conversation WHERE id > ? ORDER BY id ASC", (last_id,))
                        rows = cursor.fetchall()
                        
                        for row in rows:
                            last_id = row[0]
                            data = {
                                "timestamp": row[1],
                                "role": row[2],
                                "message": row[3]
                            }
                            yield f"data: {json.dumps(data)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            time.sleep(1)
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    print(f"🌐 Dashboard starting at http://{HOST}:{PORT}")
    print("🔒 Binding to localhost only (security requirement)")
    
    # Start Flask app
    app.run(host=HOST, port=PORT, debug=False)
