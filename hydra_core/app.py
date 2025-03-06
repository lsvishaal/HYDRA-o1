import redis
import json
import os
import sys
import time
import logging
import subprocess
from flask import Flask, Response, request, jsonify
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Environment Variables
REDIS_HOST = os.getenv("REDIS_HOST", "hydra_redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
LOG_FILE = "/var/log/hydra/flask_logs.json"

# Set up Redis connection
try:
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    redis_client.ping()
    print("[✅] Connected to Redis Successfully!")
except redis.ConnectionError as e:
    print(f"[❌] Redis Connection Failed: {e}")
    sys.exit(1)

# Setup structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log_handler = logging.FileHandler(LOG_FILE, "a")
log_handler.setLevel(logging.INFO)
app.logger.addHandler(log_handler)

# Prometheus Metric
REQUEST_COUNT = Counter('flask_app_request_count_total', 'Total HTTP requests received')

def log_to_redis_and_file(log_data):
    """
    Publishes structured logs to Redis Stream 'flask_logs' and a local JSON file.
    """
    try:
        redis_client.xadd("flask_logs", {"log": json.dumps(log_data)}, maxlen=2000)  # Retain last 2000 logs
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_data) + "\n")
        print(f"[Producer] Log Published: {json.dumps(log_data, ensure_ascii=False)}")
    except Exception as e:
        print(f"[Error] Redis Logging Failed: {str(e)}")

@app.route('/health')
def health():
    """
    Health check that verifies:
    - Redis connectivity
    - Gunicorn worker status
    """
    try:
        redis_status = "healthy" if redis_client.ping() else "unhealthy"
    except Exception:
        redis_status = "unhealthy"

    # Check Gunicorn workers with `pgrep`
    try:
        gunicorn_workers = int(subprocess.getoutput("pgrep -c gunicorn").strip())
    except ValueError:
        gunicorn_workers = 0  # If error, assume no workers are running

    worker_status = "healthy" if gunicorn_workers >= 2 else "unhealthy"

    response = {
        "status": "healthy" if redis_status == "healthy" and worker_status == "healthy" else "unhealthy",
        "redis_status": redis_status,
        "workers": gunicorn_workers
    }

    log_to_redis_and_file({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "level": "INFO",
        "message": "Health check accessed",
        "request": request.path,
        "health_status": response
    })

    return jsonify(response), 200 if response["status"] == "healthy" else 500

@app.before_request
def before_request():
    REQUEST_COUNT.inc()
    log_to_redis_and_file({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "level": "INFO",
        "message": f"Received request: {request.path}",
        "request": request.path
    })

@app.route('/metrics')
def metrics():
    """
    Expose Prometheus metrics.
    """
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    from gunicorn.app.base import BaseApplication

    class GunicornApp(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                self.cfg.set(key, value)

        def load(self):
            return self.application

    options = {
        "bind": "0.0.0.0:5000",
        "workers": 4,
        "timeout": 120,
        "graceful_timeout": 60,
        "keepalive": 10,
    }

    GunicornApp(app, options).run()
