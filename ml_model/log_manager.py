import json
import os
import time
from datetime import datetime, timedelta

# Constants
LOG_FILE = "logs/training_logs.json"
RETENTION_DAYS = 365  # Keep logs for 1 year
MINIMUM_LOGS_TO_KEEP = 500  # Even after pruning, retain at least this many
TRAINING_THRESHOLD = 100  # Retrain if at least 100 new logs exist

def load_logs():
    """Load existing logs from the JSON file."""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_logs(logs):
    """Save logs back to the JSON file."""
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def add_log(entry):
    """Add a new log entry."""
    logs = load_logs()
    logs.append(entry)
    save_logs(logs)

def prune_old_logs():
    """Remove logs older than RETENTION_DAYS while keeping the most recent MINIMUM_LOGS_TO_KEEP."""
    logs = load_logs()
    if not logs:
        return

    cutoff_time = datetime.now() - timedelta(days=RETENTION_DAYS)
    logs = [log for log in logs if datetime.strptime(log["timestamp"], "%Y-%m-%d %H:%M:%S") >= cutoff_time]

    if len(logs) < MINIMUM_LOGS_TO_KEEP:
        return  # Prevent excessive deletion

    save_logs(logs)

def should_retrain():
    """Check if enough new logs exist to trigger retraining."""
    logs = load_logs()
    return len(logs) >= TRAINING_THRESHOLD

if __name__ == "__main__":
    prune_old_logs()
    print(f"✅ Pruned old logs. Current log count: {len(load_logs())}")
