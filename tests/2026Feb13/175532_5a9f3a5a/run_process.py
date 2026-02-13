import json
from data_processor import process_data

def main():
    raw_data = {"name": "hybrid", "type": "orchestrator", "version": 7}
    processed = process_data(raw_data)
    print(json.dumps(processed))
    return "HYBRID" in processed.values()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)