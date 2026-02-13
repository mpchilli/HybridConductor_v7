from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import time
import json
import random
import threading
import queue
import os

# Add static folder config for serving React build
app = Flask(__name__, static_folder='../static', static_url_path='')
CORS(app)

# Global event queue for broadcasting to all clients
event_queue = queue.Queue()

# Global state for task simulation
task_state = {
    "tasks": [
        {"id": 1, "name": "Orchestrator Init", "status": "completed"},
        {"id": 2, "name": "Data Ingestion", "status": "running"},
        {"id": 3, "name": "Model Training", "status": "pending"}
    ],
    "logs": [
        f"Log entry {int(time.time())}: System check OK"
    ]
}

def generate_sample_data():
    """Generates sample data and puts it into the queue."""
    while True:
        # Simulate some random updates to validation stats
        data = {
            "type": "update",
            "timestamp": time.time(),
            "cpu_usage": random.randint(10, 90),
            "memory_usage": random.randint(20, 80),
            "active_tasks": len([t for t in task_state["tasks"] if t["status"] == "running"]),
            "tasks": task_state["tasks"],
            "logs": task_state["logs"][-50:] # Keep last 50 logs
        }
        event_queue.put(data)
        time.sleep(1)

# Start generator thread
threading.Thread(target=generate_sample_data, daemon=True).start()

def sse_generator():
    """Yields events from the queue to the client."""
    while True:
        try:
            # Get data from queue, blocking until available
            data = event_queue.get()
            yield f"data: {json.dumps(data)}\n\n"
        except Exception as e:
            print(f"Stream error: {e}")
            break

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/stream')
def stream():
    return Response(sse_generator(), mimetype='text/event-stream')

@app.route('/api/stats', methods=['GET'])
def stats():
    return jsonify({
        "status": "online",
        "uptime": "24h 12m",
        "version": "8.0.0"
    })

@app.route('/api/console', methods=['POST'])
def console():
    data = request.json
    command = data.get('command', '')
    
    # Add log entry
    timestamp = time.time()
    log_message = f"User command: {command}"
    task_state["logs"].append({
        "type": "INFO",
        "message": log_message,
        "timestamp": timestamp
    })
    
    if command:
        if "landing page" in command.lower():
            # Complex task simulation
            root_id = max([t["id"] for t in task_state["tasks"]]) + 1 if task_state["tasks"] else 1
            main_task = {
                "id": root_id, 
                "name": f"Project: {command}", 
                "status": "running",
                "children": [
                    {"id": root_id + 1, "name": "Strategic Discovery", "status": "completed", "details": "Analyzing target audience and competitive landscape."},
                    {"id": root_id + 2, "name": "Brand Identity Design", "status": "running", "children": [
                        {"id": root_id + 3, "name": "Color Palette Generation", "status": "completed"},
                        {"id": root_id + 4, "name": "Typography Selection", "status": "running"}
                    ]},
                    {"id": root_id + 5, "name": "Module Engineering", "status": "pending", "children": [
                        {"id": root_id + 6, "name": "Interactive Hero Section", "status": "pending"},
                        {"id": root_id + 7, "name": "Responsive Grid Layout", "status": "pending"}
                    ]}
                ] 
            }
            task_state["tasks"].append(main_task)
            
            # Simulate progress
            def run_complex_sim():
                time.sleep(2)
                update_subtask_status(root_id, root_id + 4, "completed")
                update_subtask_status(root_id, root_id + 2, "completed")
                update_subtask_status(root_id, root_id + 5, "running")
                update_subtask_status(root_id, root_id + 6, "running")
                
                time.sleep(3)
                update_subtask_status(root_id, root_id + 6, "completed")
                update_subtask_status(root_id, root_id + 7, "running")
                
                time.sleep(2)
                update_subtask_status(root_id, root_id + 7, "completed")
                update_subtask_status(root_id, root_id + 5, "completed")
                main_task["status"] = "completed"
                
                # Generate Mock Output
                output_dir = os.path.join(app.static_folder, 'output')
                os.makedirs(output_dir, exist_ok=True)
                with open(os.path.join(output_dir, 'coffee-shop.html'), 'w') as f:
                    f.write("<html><body style='background:#111; color:#fff; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh;'>")
                    f.write("<div><h1 style='color:#b91c1c;'>Mocha Orchestrator Dashboard</h1><p>Baked fresh by Ralph v8.0</p></div>")
                    f.write("</body></html>")
                
                task_state["logs"].append({
                    "type": "SUCCESS",
                    "message": "Deployment complete! Preview at /output/coffee-shop.html",
                    "timestamp": time.time()
                })

            threading.Thread(target=run_complex_sim, daemon=True).start()
        else:
            # Simple task simulation
            new_task_id = max([t["id"] for t in task_state["tasks"]]) + 1 if task_state["tasks"] else 1
            new_task = {
                "id": new_task_id, 
                "name": f"Task: {command}", 
                "status": "pending",
                "children": [] 
            }
            task_state["tasks"].append(new_task)
            threading.Timer(1.0, lambda: update_task_status(new_task_id, "running")).start()
            threading.Timer(4.0, lambda: update_task_status(new_task_id, "completed")).start()

    return jsonify({
        "command": command,
        "output": f"Orchestrating: {command}",
        "status": "success"
    })

@app.route('/api/reset', methods=['POST'])
def reset():
    global task_state
    task_state = {
        "tasks": [],
        "logs": [f"Session reset at {time.strftime('%H:%M:%S')}"]
    }
    # Optional: Clear queue or broadcast a 'reset' event
    event_queue.put({"type": "reset", "timestamp": time.time()})
    return jsonify({"status": "success", "message": "Session reset"})

def update_task_status(task_id, status):
    for task in task_state["tasks"]:
        if task["id"] == task_id:
            task["status"] = status
            break

def update_subtask_status(root_id, subtask_id, status):
    """Deep search for subtask to update status."""
    def _find_and_update(tasks):
        for t in tasks:
            if t["id"] == subtask_id:
                t["status"] = status
                return True
            if "children" in t and _find_and_update(t["children"]):
                return True
        return False
    _find_and_update(task_state["tasks"])


if __name__ == '__main__':
    print("Starting Ralph Dashboard Backend...")
    print("Verify at http://localhost:5000")
    app.run(debug=True, port=5000, threaded=True)

