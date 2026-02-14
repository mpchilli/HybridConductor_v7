import os
import ssl
import sys
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Mock config loading
PROJECT_ROOT = Path(".").resolve()
sys.path.insert(0, str(PROJECT_ROOT))
from notifier import _load_notification_config

def test_telegram_ssl():
    print("Testing Telegram SSL Connection...")
    config = _load_notification_config(PROJECT_ROOT)
    token = config.get("telegram_bot_token")
    
    if not token or ":" not in token:
        print("SKIP: No valid Telegram token found in config")
        return

    url = f"https://api.telegram.org/bot{token}/getMe"
    print(f"Connecting to {url}...")
    
    # Method 1: Default urlopen (failed previously)
    print("\nAttempt 1: Default urlopen")
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=10) as resp:
            print("SUCCESS: Connected!")
            print(json.loads(resp.read().decode("utf-8")))
    except Exception as e:
        print(f"FAILED: {e}")

    # Method 2: ssl.create_default_context (my previous fix)
    print("\nAttempt 2: ssl.create_default_context()")
    try:
        ctx = ssl.create_default_context()
        req = Request(url, method="GET")
        with urlopen(req, timeout=10, context=ctx) as resp:
            print("SUCCESS: Connected!")
    except Exception as e:
        print(f"FAILED: {e}")

    # Method 3: Force TLS 1.2
    print("\nAttempt 3: PROTOCOL_TLSv1_2")
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        req = Request(url, method="GET")
        with urlopen(req, timeout=10, context=ctx) as resp:
            print("SUCCESS: Connected!")
    except Exception as e:
        print(f"FAILED: {e}")
        
    # Method 4: Bypass hostname check (insecure, just for diag)
    print("\nAttempt 4: No verify (Insecure)")
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = Request(url, method="GET")
        with urlopen(req, timeout=10, context=ctx) as resp:
            print("SUCCESS: Connected!")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_telegram_ssl()
