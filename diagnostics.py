
# diagnostics.py
import os
import ssl
import urllib.request
import sys
from pathlib import Path

print("=== HybridConductor Windows Diagnostics ===\n")

# 1. Check localhost accessibility
print("[1] Testing localhost:5000 accessibility...")
try:
    # Use unverified context just to check connectivity (ignoring certs for localhost)
    ctx = ssl._create_unverified_context()
    urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2, context=ctx)
    print("    ✓ Flask backend reachable")
except Exception as e:
    print(f"    ✗ Flask unreachable: {e}")
    print("    (Note: This is expected if the backend isn't running yet)")

# 2. Check Discord config
print("\n[2] Discord configuration check...")
webhook = os.getenv('DISCORD_WEBHOOK_URL', '')
if not webhook:
    # Try loading from .env
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('DISCORD_WEBHOOK_URL='):
                    webhook = line.split('=', 1)[1].strip()
    except:
        pass

if not webhook:
    print("    ⚠ DISCORD_WEBHOOK_URL not set (optional - notifications disabled)")
elif not webhook.startswith('https://discord.com/api/webhooks/'):
    print(f"    ✗ Invalid webhook format: {webhook[:30]}...")
else:
    print("    ✓ Webhook URL format valid")

# 3. Check cert bundle
print("\n[3] Certificate bundle check...")
cert_path = Path('vendor/certifi/cacert.pem')
if cert_path.exists():
    print(f"    ✓ Cert bundle found ({cert_path.stat().st_size} bytes)")
    
    # Verify we can load it
    try:
        ctx = ssl.create_default_context(cafile=str(cert_path))
        print("    ✓ SSL Context creation successful with bundle")
    except Exception as e:
        print(f"    ✗ Failed to create SSL context with bundle: {e}")
else:
    print(f"    ✗ Missing cert bundle at {cert_path.absolute()}")
    print("    → Run: curl -L https://curl.se/ca/cacert.pem -o vendor/certifi/cacert.pem")

# 4. Check pywebview renderer preference
print("\n[4] Renderer compatibility check...")
gui_env = os.environ.get('PYWEBVIEW_GUI')
print(f"    PYWEBVIEW_GUI env var: {gui_env}")

if gui_env == 'winforms':
    print("    ✓ WinForms renderer selected (Windows-safe)")
else:
    print("    ⚠ No specific renderer forced in environment")
    print("    → start_gui.py should force 'winforms' to avoid crashes")


# 5. Check Package Integrity
print("\n[5] Package Integrity Check...")
try:
    from hybridconductor.core import LoopGuardian
    print("    ✓ hybridconductor.core.LoopGuardian importable")
except ImportError as e:
    print(f"    ✗ Failed to import LoopGuardian from hybridconductor.core: {e}")

print("\n=== Diagnostics Complete ===")
