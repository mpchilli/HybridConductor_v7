import pytest
import json
import sys
import os

# Ensure we can import the app
sys.path.append(os.getcwd())

from dashboard.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_stats_endpoint(client):
    """Test the stats endpoint returns valid JSON."""
    rv = client.get('/api/stats')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert "uptime" in data
    assert "status" in data
    assert data["status"] == "online"

def test_console_endpoint(client):
    """Test the console endpoint echoes commands."""
    rv = client.post('/api/console', json={"command": "ping"})
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["command"] == "ping"
    assert "Executed: ping" in data["output"]

def test_stream_endpoint(client):
    """Test the SSE stream endpoint."""
    rv = client.get('/api/stream')
    assert rv.status_code == 200
    assert 'text/event-stream' in rv.headers['Content-Type']
    
    # Consume a bit of the stream to verify format
    # The flask test client response is an iterable
    # We check if we get at least one "data:" line
    found_data = False
    limit = 5
    for i, chunk in enumerate(rv.response):
        if i > limit: 
            break
        if b"data:" in chunk:
            found_data = True
            break
            
    assert found_data, "Stream did not return data: ... lines"
