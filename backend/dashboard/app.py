from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import time
import json
import random
import threading
import queue

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
    
    # Simulate adding a task based on command
    if command:
        new_task_id = max([t["id"] for t in task_state["tasks"]]) + 1 if task_state["tasks"] else 1
        new_task = {
            "id": new_task_id, 
            "name": f"Task: {command}", 
            "status": "pending",
            "children": [] 
        }
        task_state["tasks"].append(new_task)
        
        # Simulate swift execution start
        threading.Timer(1.0, lambda: update_task_status(new_task_id, "running")).start()
        threading.Timer(4.0, lambda: update_task_status(new_task_id, "completed")).start()

    return jsonify({
        "command": command,
        "output": f"Scheduled: {command}",
        "status": "success"
    })

def update_task_status(task_id, status):
    for task in task_state["tasks"]:
        if task["id"] == task_id:
            task["status"] = status
            break

if __name__ == '__main__':
    print("Starting Ralph Dashboard Backend...")
    print("Verify at http://localhost:5000")
    app.run(debug=True, port=5000, threaded=True)

