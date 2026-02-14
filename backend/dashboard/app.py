"""
app.py - Dashboard Backend with Real Orchestrator Bridge & Verbose Logging

Replaces mock/simulation logic with:
1. Real orchestrator subprocess execution via bridge
2. Verbose real-time log streaming via SSE
3. Process flow state tracking with timestamps and repeat counts
4. DRY version sourcing from PROJECT_ROOT/VERSION
"""
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import time
import json
import threading
import queue
import os
import sys
import yaml
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# ─── Project Root & Version (DRY) ───────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))  # Allow importing notifier.py from project root

def _read_version():
    """Read version from single source of truth: PROJECT_ROOT/VERSION"""
    version_file = PROJECT_ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"

APP_VERSION = _read_version()

# ─── Static File Resolution ────────────────────────────────────────────────
def get_resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(base_path, relative_path)
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', os.path.basename(relative_path)))

static_dir = get_resource_path('static')
app = Flask(__name__, static_folder=static_dir, static_url_path='')
CORS(app)

# ─── Logging Setup ──────────────────────────────────────────────────────────
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("dashboard")

# ─── Global State ───────────────────────────────────────────────────────────
# Event queue for SSE broadcast
event_queue = queue.Queue()

# Process flow stages (matches orchestrator.py State enum)
FLOW_STAGES = ["planning", "building", "verifying", "debugging", "complete", "failed"]

# Verbose log buffer (thread-safe)
log_buffer_lock = threading.Lock()

# Real application state
app_state = {
    "version": APP_VERSION,
    "tasks": [],
    "logs": [],
    "process_flow": {
        "current_stage": None,
        "stages": {stage: {"count": 0, "completed": False, "timestamps": []} for stage in FLOW_STAGES},
        "history": [],  # [{timestamp, stage, event}]
        "error": None,
    },
    "orchestrator_pid": None,
    "config": {
        "temperature": 70,
        "detail": 90,
        "context_window": 50,
        "verbose": True,
    }
}

# ─── Notification Integration ───────────────────────────────────────────────
try:
    from notifier import NotificationManager
    _notifier = NotificationManager(PROJECT_ROOT, command_handler=None)
    if _notifier.enabled:
        logger.info("Notifications enabled (Discord/Telegram)")
        _notifier.start_polling()
    else:
        logger.info("Notifications not configured — skipping")
except ImportError:
    _notifier = None
    logger.warning("notifier.py not found — notifications disabled")

def _add_log(level, message):
    """Thread-safe log append + push to SSE."""
    entry = {
        "type": level.upper(),
        "message": message,
        "timestamp": time.time() * 1000  # JS-compatible ms
    }
    with log_buffer_lock:
        app_state["logs"].append(entry)
        # Keep last 500 logs
        if len(app_state["logs"]) > 500:
            app_state["logs"] = app_state["logs"][-500:]
    logger.log(getattr(logging, level.upper(), logging.INFO), message)

def _update_flow_stage(stage, event="entered"):
    """Update process flow tracking + send notification."""
    now = datetime.now().isoformat()
    flow = app_state["process_flow"]
    flow["current_stage"] = stage
    flow["error"] = None

    if stage in flow["stages"]:
        flow["stages"][stage]["count"] += 1
        flow["stages"][stage]["timestamps"].append(now)
        if event == "completed":
            flow["stages"][stage]["completed"] = True

    flow["history"].append({
        "timestamp": now,
        "stage": stage,
        "event": event
    })
    # Keep last 200 history entries
    if len(flow["history"]) > 200:
        flow["history"] = flow["history"][-200:]

    # Send notification
    if _notifier and _notifier.enabled:
        notify_status = stage if event != "error" else "failed"
        _notifier.notify(notify_status, f"Stage: {stage} ({event})", stage=stage)

def _broadcast_state():
    """Push current state to all SSE clients."""
    data = {
        "type": "update",
        "timestamp": time.time(),
        "version": app_state["version"],
        "tasks": app_state["tasks"],
        "logs": app_state["logs"][-100:],
        "process_flow": app_state["process_flow"],
        "config": app_state["config"],
        "orchestrator_running": app_state["orchestrator_pid"] is not None,
    }
    try:
        event_queue.put_nowait(data)
    except queue.Full:
        pass  # Drop if queue is full

# ─── SSE Heartbeat (replaces generate_sample_data) ─────────────────────────
def _heartbeat_loop():
    """Sends state updates every 2 seconds instead of fake data."""
    while True:
        _broadcast_state()
        time.sleep(2)

threading.Thread(target=_heartbeat_loop, daemon=True).start()

# ─── Orchestrator Bridge ───────────────────────────────────────────────────
def _run_orchestrator(command, complexity="streamlined"):
    """
    Run the real orchestrator as a subprocess and stream its output.
    This replaces ALL mock task simulation.
    """
    _add_log("INFO", f"▶ Orchestrator starting: '{command}' (mode: {complexity})")
    _update_flow_stage("planning", "entered")

    orchestrator_path = PROJECT_ROOT / "orchestrator.py"
    python_exe = sys.executable

    if not orchestrator_path.exists():
        error_msg = f"orchestrator.py not found at {orchestrator_path}"
        _add_log("ERROR", error_msg)
        _update_flow_stage("failed", "error")
        app_state["process_flow"]["error"] = error_msg
        return

    # Build task tree
    task_id = int(time.time() * 1000) % 100000
    root_task = {
        "id": task_id,
        "name": f"Task: {command[:80]}",
        "status": "running",
        "children": [
            {"id": task_id + 1, "name": "Planning", "status": "running", "children": []},
            {"id": task_id + 2, "name": "Building", "status": "pending", "children": []},
            {"id": task_id + 3, "name": "Verifying", "status": "pending", "children": []},
        ]
    }
    app_state["tasks"].append(root_task)
    _broadcast_state()

    try:
        process = subprocess.Popen(
            [python_exe, str(orchestrator_path), "--prompt", command, "--complexity", complexity],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(PROJECT_ROOT),
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        app_state["orchestrator_pid"] = process.pid
        _add_log("DEBUG", f"Orchestrator PID: {process.pid}")

        # Stream stdout line by line
        for line in iter(process.stdout.readline, ''):
            line = line.rstrip()
            if not line:
                continue

            # Detect state transitions from orchestrator output
            line_lower = line.lower()
            if "entering state:" in line_lower or "state:" in line_lower:
                for stage in FLOW_STAGES:
                    if stage in line_lower:
                        _update_flow_stage(stage, "entered")
                        # Update task tree
                        stage_map = {"planning": 1, "building": 2, "verifying": 3}
                        if stage in stage_map:
                            offset = stage_map[stage]
                            for child in root_task.get("children", []):
                                if child["id"] == task_id + offset:
                                    child["status"] = "running"
                                elif child["id"] < task_id + offset:
                                    child["status"] = "completed"
                        break

            # Classify log level from content
            if "error" in line_lower or "critical" in line_lower or "failed" in line_lower:
                _add_log("ERROR", line)
            elif "warning" in line_lower or "warn" in line_lower:
                _add_log("WARN", line)
            elif "debug" in line_lower or "trace" in line_lower:
                _add_log("DEBUG", line)
            else:
                _add_log("INFO", line)

            _broadcast_state()

        process.wait()
        exit_code = process.returncode

        if exit_code == 0:
            _add_log("INFO", "✓ Orchestrator completed successfully")
            _update_flow_stage("complete", "completed")
            root_task["status"] = "completed"
            for child in root_task.get("children", []):
                child["status"] = "completed"
        else:
            _add_log("ERROR", f"✕ Orchestrator exited with code {exit_code}")
            _update_flow_stage("failed", "error")
            app_state["process_flow"]["error"] = f"Exit code: {exit_code}"
            root_task["status"] = "failed"

    except FileNotFoundError:
        error_msg = f"Python executable not found: {python_exe}"
        _add_log("ERROR", error_msg)
        _update_flow_stage("failed", "error")
        app_state["process_flow"]["error"] = error_msg
        root_task["status"] = "failed"
    except Exception as e:
        error_msg = f"Orchestrator bridge error: {str(e)}"
        _add_log("ERROR", error_msg)
        _update_flow_stage("failed", "error")
        app_state["process_flow"]["error"] = error_msg
        root_task["status"] = "failed"
    finally:
        app_state["orchestrator_pid"] = None
        _broadcast_state()


# ─── SSE Generator ──────────────────────────────────────────────────────────
def sse_generator():
    """Yields events from the queue to the client."""
    # Send initial state immediately
    yield f"data: {json.dumps({'type': 'init', 'version': APP_VERSION, 'process_flow': app_state['process_flow'], 'config': app_state['config']})}\n\n"
    while True:
        try:
            data = event_queue.get(timeout=30)
            yield f"data: {json.dumps(data)}\n\n"
        except queue.Empty:
            # Send keepalive
            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            break


# ─── Routes ─────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/stream')
def stream():
    return Response(sse_generator(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/api/version')
def version():
    return jsonify({"version": APP_VERSION})

@app.route('/api/stats', methods=['GET'])
def stats():
    return jsonify({
        "status": "online",
        "version": APP_VERSION,
        "orchestrator_running": app_state["orchestrator_pid"] is not None,
        "log_count": len(app_state["logs"]),
        "task_count": len(app_state["tasks"]),
    })

@app.route('/api/console', methods=['POST'])
def console():
    data = request.json
    command = data.get('command', '')
    complexity = data.get('complexity', 'streamlined')

    if not command.strip():
        return jsonify({"error": "Empty command"}), 400

    _add_log("INFO", f"▶ User command: {command}")

    # Check if orchestrator is already running
    if app_state["orchestrator_pid"] is not None:
        _add_log("WARN", "Orchestrator is already running. Wait for completion or reset.")
        return jsonify({"error": "Orchestrator already running", "status": "busy"}), 409

    # Run orchestrator in background thread
    thread = threading.Thread(
        target=_run_orchestrator,
        args=(command, complexity),
        daemon=True
    )
    thread.start()

    return jsonify({
        "command": command,
        "status": "started",
        "message": f"Orchestrating: {command}"
    })

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        new_config = request.json
        if new_config:
            app_state["config"].update(new_config)
            _add_log("INFO", f"Config updated: {json.dumps(new_config)}")
        return jsonify(app_state["config"])
    else:
        # Try loading from YAML, merge with runtime
        config_path = PROJECT_ROOT / "config" / "default.yml"
        file_config = {}
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    file_config = yaml.safe_load(f) or {}
            except Exception:
                pass
        return jsonify({**file_config, **app_state["config"], "version": APP_VERSION})

@app.route('/api/process-flow', methods=['GET'])
def process_flow():
    """Dedicated endpoint for process flow state."""
    return jsonify(app_state["process_flow"])

@app.route('/api/reset', methods=['POST'])
def reset():
    # Kill orchestrator if running
    if app_state["orchestrator_pid"]:
        try:
            import signal
            os.kill(app_state["orchestrator_pid"], signal.SIGTERM)
            _add_log("WARN", f"Killed orchestrator PID {app_state['orchestrator_pid']}")
        except Exception:
            pass
        app_state["orchestrator_pid"] = None

    app_state["tasks"] = []
    app_state["logs"] = []
    app_state["process_flow"] = {
        "current_stage": None,
        "stages": {stage: {"count": 0, "completed": False, "timestamps": []} for stage in FLOW_STAGES},
        "history": [],
        "error": None,
    }

    _add_log("INFO", f"Session reset at {datetime.now().strftime('%H:%M:%S')}")
    _broadcast_state()
    return jsonify({"status": "success", "message": "Session reset"})

@app.route('/api/presets', methods=['GET'])
def get_presets():
    config_path = PROJECT_ROOT / "config" / "default.yml"
    if not config_path.exists():
        return jsonify([])
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            return jsonify(config.get("presets", []))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print(f"Starting Hybrid Conductor Dashboard v{APP_VERSION}...")
    print(f"Verify at http://localhost:5000")
    app.run(debug=True, port=5000, threaded=True)
