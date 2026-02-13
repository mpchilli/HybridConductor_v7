from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import time
import json
import random
import threading
import queue

app = Flask(__name__)
CORS(app)

# Global event queue for broadcasting to all clients
event_queue = queue.Queue()

def generate_sample_data():
    """Generates sample data and puts it into the queue."""
    while True:
        data = {
            "type": "update",
            "timestamp": time.time(),
            "cpu_usage": random.randint(10, 90),
            "memory_usage": random.randint(20, 80),
            "active_tasks": random.randint(1, 5),
            "tasks": [
                {"id": 1, "name": "Orchestrator Init", "status": "completed"},
                {"id": 2, "name": "Data Ingestion", "status": "running" if random.random() > 0.5 else "pending"},
                {"id": 3, "name": "Model Training", "status": "pending"}
            ],
            "logs": [
                f"Log entry {int(time.time())}: System check OK",
                f"Log entry {int(time.time())}: Heartbeat received"
            ]
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
            # Note: In a real multi-client app, we'd need a pub/sub system or individual queues
            # For this simple dashboard, we just generate fresh data or use a broadcast mechanism
            # Here we simulate a stream by just yielding generated data directly for each client
            # to avoid queue contention issues in this simple example.
            
            data = {
                "type": "update",
                "timestamp": time.time(),
                "cpu": random.randint(5, 95),
                "memory": random.randint(30, 70),
                "log": f"System active at {time.strftime('%H:%M:%S')}"
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(1)
        except Exception as e:
            print(f"Stream error: {e}")
            break

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
    # Simulate command execution
    return jsonify({
        "command": command,
        "output": f"Executed: {command}",
        "status": "success"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)
