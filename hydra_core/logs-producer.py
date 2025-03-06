import redis
import json
import os
import time

# Redis connection
redis_host = os.getenv("REDIS_HOST", "hydra_redis")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

def log_to_redis(log_data):
    """
    Publishes logs to Redis Stream 'flask_logs'.
    """
    redis_client.xadd("flask_logs", log_data)
    print(f"[Producer] Log Published: {json.dumps(log_data)}")

if __name__ == "__main__":
    for i in range(5):
        sample_log = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "level": "INFO",
            "message": f"Sample log {i}",
        }
        log_to_redis(sample_log)
        time.sleep(2)
