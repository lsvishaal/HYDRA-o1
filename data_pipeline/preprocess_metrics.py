import redis
import json
import time

# Redis Connection Settings
REDIS_HOST = "hydra_redis"
REDIS_PORT = 6379
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def consume_logs():
    """
    Continuously listens to the Redis Stream 'flask_logs' and processes logs.
    """
    print("[Consumer] Listening for logs...")
    last_id = '0'  # Start from the beginning
    while True:
        try:
            logs = redis_client.xread({"flask_logs": last_id}, count=5, block=5000)  # Read up to 5 logs
            if logs:
                for stream, messages in logs:
                    for message_id, message in messages:
                        log_data = json.loads(message["log"])
                        print(f"[Consumer] Processed Log: {json.dumps(log_data, ensure_ascii=False)}")
                        last_id = message_id  # Update last processed log ID
        except redis.ConnectionError as e:
            print(f"[❌] Redis Connection Failed: {e}")
            time.sleep(5)  # Retry after 5s
        except Exception as e:
            print(f"[Error] Redis Read Failed: {str(e)}")

if __name__ == "__main__":
    consume_logs()
