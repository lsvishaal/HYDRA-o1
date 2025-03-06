import redis
import json
import time
from flask import Flask, jsonify
from threading import Thread

# Redis Connection
REDIS_HOST = "hydra_redis"
REDIS_PORT = 6379
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the data pipeline."""
    return jsonify({"status": "healthy"}), 200

def is_valid_log(log_data):
    """Filter out logs that are not useful for ML training."""
    # Ignore Prometheus /metrics logs and logs missing "features"
    if log_data.get("request") in ["/metrics", "/health"]:
        return False  
    if "features" not in log_data:
        print(f"[🚫 Skipping Non-Feature Log] {json.dumps(log_data, ensure_ascii=False)}")
        return False  
    return True

def consume_logs():
    print("[Consumer] Listening for logs...")
    last_id = '0'

    while True:
        try:
            logs = redis_client.xread({"flask_logs": last_id}, count=10, block=5000)
            if logs:
                for stream, messages in logs:
                    for message_id, message in messages:
                        try:
                            log_data = json.loads(message["log"])
                            
                            if is_valid_log(log_data):
                                print(f"[✅ Consumer] Processing Log: {json.dumps(log_data, ensure_ascii=False)}")
                                
                            # Update last processed log ID
                            last_id = message_id  

                        except json.JSONDecodeError:
                            print(f"[❌] Invalid JSON Log Skipped: {message}")

            else:
                print("[🔍] No new logs found in Redis stream.")

        except redis.ConnectionError as e:
            print(f"[❌] Redis Connection Failed: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"[Error] Redis Read Failed: {str(e)}")


if __name__ == "__main__":
    log_thread = Thread(target=consume_logs, daemon=True)
    log_thread.start()
    app.run(host="0.0.0.0", port=8000)
