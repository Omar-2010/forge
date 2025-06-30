import os
import sys
from waitress import serve

INSTANCE_DIR = os.path.join(os.path.dirname(__file__), 'instance')
PORT_FILE = os.path.join(INSTANCE_DIR, 'last_port.txt')
WSGI_APP = 'wsgi:app'
DEFAULT_PORT = 5096

# Ensure instance dir exists
os.makedirs(INSTANCE_DIR, exist_ok=True)

# Read last used port
if os.path.exists(PORT_FILE):
    with open(PORT_FILE, 'r') as f:
        try:
            last_port = int(f.read().strip())
        except Exception:
            last_port = DEFAULT_PORT
else:
    last_port = DEFAULT_PORT

# Increment port
new_port = last_port + 1
with open(PORT_FILE, 'w') as f:
    f.write(str(new_port))

print(f"[INFO] Starting Waitress WSGI server on port {new_port}...")

# Import the app from wsgi.py
try:
    from wsgi import app
except ImportError:
    print("[ERROR] Could not import 'app' from wsgi.py. Make sure it exists and is correct.")
    sys.exit(1)

serve(app, host='0.0.0.0', port=new_port)
