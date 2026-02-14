
import ssl
import certifi # This will be our vendored module or we will point to the file directly if certifi lib isn't installed but the pem is there.
# Wait, the plan was to vendor 'certifi' package or just the pem? 
# The feedback says: "from pathlib import Path... cert_path = Path(__file__).parent.parent / 'vendor' / 'certifi' / 'cacert.pem'"
# But also "pip install certifi --target=./vendor".
# If we just curl key, we can point to it directly.

from pathlib import Path
import os

def patch_ssl_context():
    """Force Python to use locally vendored Mozilla's cert bundle"""
    # Assuming file structure: hybridconductor/core/ssl_fix.py -> root/vendor/certifi/cacert.pem
    # hybridconductor/core/../../vendor/certifi/cacert.pem
    
    project_root = Path(__file__).parent.parent.parent
    cert_path = project_root / "vendor" / "certifi" / "cacert.pem"
  
    if cert_path.exists():
        # print(f"DEBUG: Loading certs from {cert_path}")
        ssl_context = ssl.create_default_context(cafile=str(cert_path))
        # Explicitly enable modern protocols
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')  # Windows compat
        return ssl_context
    else:
        # print("DEBUG: Vendored certs not found, using system default")
        return ssl.create_default_context()  # Fallback
