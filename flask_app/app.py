import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from flask import Flask, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter

app = Flask(__name__)

# Define log directory inside the container
log_dir = "/var/log/hydra"
log_file = os.path.join(log_dir, "flask_app.log")

# Ensure the log directory exists with correct permissions
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)
    os.chmod(log_dir, 0o777)  # Ensure it's writable inside Docker

# Configure log handler
file_handler = RotatingFileHandler(log_file, maxBytes=1000000, backupCount=3, delay=True)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)

# Also log to stdout for debugging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
app.logger.addHandler(console_handler)

app.logger.setLevel(logging.INFO)
app.logger.propagate = False  # Prevent duplicate logs

# Log when the app starts
app.logger.info("✅ Flask Logging Initialized & Writing to /var/log/hydra/flask_app.log")

# Health check route
@app.route('/health')
def health():
    app.logger.info("🩺 Health check accessed")
    return "OK", 200

@app.before_request
def before_request():
    app.logger.info("➡️ Received request")

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
