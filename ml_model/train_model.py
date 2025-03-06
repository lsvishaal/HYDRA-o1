import json
import os
from datetime import datetime, timedelta

LOG_FILE = "/app/logs/training_logs.json"
RETENTION_DAYS = 365  # Keep logs for 1 year
MINIMUM_LOGS_TO_KEEP = 500  # Keep at least 500 logs

def prune_old_logs():
    logs = load_logs()
    cutoff_time = datetime.now() - timedelta(days=RETENTION_DAYS)
    
    logs = [log for log in logs if datetime.strptime(log["timestamp"], "%Y-%m-%d %H:%M:%S") >= cutoff_time]
    
    if len(logs) > MINIMUM_LOGS_TO_KEEP:
        logs = logs[-MINIMUM_LOGS_TO_KEEP:]  # Retain only the last 500 logs

    save_logs(logs)
    print(f"[✅] Pruned logs, remaining: {len(logs)}")

def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_logs(logs):
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

if __name__ == "__main__":
    prune_old_logs()
