# wsgi.py - Entry point for PDFForge (iLovePDF clone)
# Production-ready WSGI interface for deployment (Gunicorn, uWSGI, etc)
import os
import sys
import traceback
from app import create_app
from flask import render_template

# Allow for environment-based config (default: production)
config_name = os.getenv('FLASK_ENV', 'production')
try:
    app = create_app(config_name)
except Exception as e:
    error_message = f"[WSGI] Failed to start app: {e}"
    error_details = traceback.format_exc()
    # Minimal Flask app to show error in browser
    from flask import Flask
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'app', 'templates'))
    @app.route("/")
    def error():
        return render_template("error.html", error_message=error_message, error_details=error_details), 500
    print(error_message, file=sys.stderr)
    print(error_details, file=sys.stderr)

# Expose 'app' for WSGI servers
if __name__ == "__main__":
    from app import create_app
    app = create_app()
    app.run(host="0.0.0.0", port=5502, ssl_context=("cert.pem", "key.pem"))
