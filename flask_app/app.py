import redis
import json
import os
import sys
import time
from flask import Flask, Response, request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter

app = Flask(__name__)

# Environment Variables
REDIS_HOST = os.getenv("REDIS_HOST", "hydra_redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Prometheus Metrics
REQUEST_COUNT = Counter('flask_app_request_count', 'Total HTTP requests received')

# Attempt Redis Connection
try:
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    redis_client.ping()  # Test Redis Connection
    print("[✅] Connected to Redis Successfully!")
except redis.ConnectionError as e:
    print(f"[❌] Redis Connection Failed: {e}")
    sys.exit(1)  # Exit if Redis is unreachable

def log_to_redis(log_data):
    """
    Publishes structured logs to Redis Stream 'flask_logs'.
    """
    try:
        redis_client.xadd("flask_logs", {"log": json.dumps(log_data)})
        print(f"[Producer] Log Published: {json.dumps(log_data, ensure_ascii=False)}")
    except Exception as e:
        print(f"[Error] Redis Logging Failed: {str(e)}")

@app.route('/health')
def health():
    """
    Health check endpoint.
    """
    log_to_redis({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "level": "INFO",
        "message": "Health check accessed",
        "request": request.path
    })
    return "OK", 200

@app.before_request
def before_request():
    """
    Logs each incoming request to Redis and increments Prometheus Counter.
    """
    REQUEST_COUNT.inc()
    log_to_redis({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "level": "INFO",
        "message": f"Received request: {request.path}",
        "request": request.path
    })

@app.route('/metrics')
def metrics():
    """
    Prometheus metrics endpoint.
    """
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
