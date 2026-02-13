import json

def process_data(data):
    """Simple data processing simulation."""
    return {k: v.upper() for k, v in data.items() if isinstance(v, str)}