import json
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import time
import os
import ssl

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_discord")

def test_discord_webhook():
    # Priority: Env var > hardcoded test (if any)
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        print("❌ Error: DISCORD_WEBHOOK_URL not found in environment.")
        return False

    print(f"Testing Discord Webhook: {webhook_url[:15]}...")
    
    embed = {
        "title": "🧪 Test Notification",
        "description": "This is a test notification from the Hybrid Conductor audit.",
        "color": 0x5865F2,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "footer": {"text": "Hybrid Conductor Audit"}
    }
    
    payload = json.dumps({"embeds": [embed]}).encode("utf-8")
    
    try:
        # We'll try with a default context first
        ctx = ssl.create_default_context()
        req = Request(webhook_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        
        print("Attempting to send Discord notification...")
        with urlopen(req, timeout=10, context=ctx) as resp:
            status = resp.status
            print(f"✅ Success! Discord returned status: {status}")
            return True
            
    except (URLError, HTTPError) as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    test_discord_webhook()
