import os
import time
import json
import joblib
import numpy as np
import redis
from flask import Flask, request, jsonify
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime
from threading import Thread

# Redis Config
REDIS_HOST = os.getenv("REDIS_HOST", "hydra_redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
MODEL_PATH = "/app/model.pkl"
LOG_FILE = "/app/logs/training_logs.json"

# Initialize Redis Connection
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def load_or_train_model():
    """
    Load an existing model or train a new one if unavailable.
    """
    if os.path.exists(MODEL_PATH):
        try:
            print("[🔵] Loading Existing Model...")
            model = joblib.load(MODEL_PATH)
            print("[✅] Model Loaded Successfully!")
            return model
        except Exception as e:
            print(f"[❌] Model corrupted or incompatible! Retraining... Error: {e}")

    print("[🟢] No valid model found! Training a new model...")
    return train_new_model([])

def train_new_model(data):
    """
    Train a new model with given log data or placeholder.
    """
    if not data:
        X_train = np.random.rand(100, 5)  # Placeholder features
        y_train = np.random.randint(0, 2, 100)  # Random labels
    else:
        X_train = np.array([entry["features"] for entry in data])
        y_train = np.array([entry["label"] for entry in data])

    model = RandomForestClassifier(n_estimators=10)
    model.fit(X_train, y_train)

    joblib.dump(model, MODEL_PATH)
    print("[✅] Model trained and saved!")
    return model

def save_log(log_data):
    """
    Save logs persistently to JSON file for long-term storage.
    """
    logs = load_logs()
    logs.append(log_data)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def load_logs():
    """Load logs from JSON file, ensuring it's always valid."""
    if not os.path.exists(LOG_FILE):
        return []
    
    try:
        with open(LOG_FILE, "r") as f:
            data = f.read().strip()
            return json.loads(data) if data else []
    except (json.JSONDecodeError, ValueError):
        print("[⚠️] Log file is corrupted! Resetting...")
        with open(LOG_FILE, "w") as f:
            json.dump([], f)
        return []


def retrain_model():
    """
    Retrain model when sufficient new logs are available.
    """
    logs = load_logs()
    
    if len(logs) < 100:  # Threshold before retraining
        print(f"⚠️ Not enough new logs to retrain yet. {len(logs)} logs available.")
        return
    
    print(f"[🔄] Retraining model with {len(logs)} logs...")
    
    X_train = np.array([entry["features"] for entry in logs])
    y_train = np.array([entry["label"] for entry in logs])

    model = train_new_model(logs)
    joblib.dump(model, MODEL_PATH)
    print("[✅] Model retrained and saved!")

    # Clear logs after training
    with open(LOG_FILE, "w") as f:
        json.dump([], f)

def consume_logs():
    """
    Continuously listen to Redis Stream 'flask_logs' and process logs.
    """
    print("[🔄] Listening for logs to train model...")
    last_id = '0'
    log_buffer = []

    while True:
        try:
            logs = redis_client.xread({"flask_logs": last_id}, count=5, block=5000)
            if logs:
                for stream, messages in logs:
                    for message_id, message in messages:
                        log_data = json.loads(message["log"])
                        last_id = message_id  

                        print(f"[🟡] Received Log: {log_data}")  
                        log_buffer.append(log_data)
                        save_log(log_data)

                        if len(log_buffer) >= 100:
                            retrain_model()
                            log_buffer.clear()

        except redis.ConnectionError as e:
            print(f"[❌] Redis Connection Failed: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"[Error] Redis Read Failed: {str(e)}")

# Initialize Flask App
app = Flask(__name__)
model = load_or_train_model()

@app.route('/predict', methods=['POST'])
def predict():
    """
    API Endpoint: Receives feature data and returns a prediction.
    """
    try:
        data = request.get_json()
        features = np.array(data["features"]).reshape(1, -1)
        prediction = model.predict(features)[0]

        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "features": data["features"],
            "label": int(prediction)
        }
        save_log(log_entry)

        return jsonify({"prediction": int(prediction)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@app.route('/prediction-metrics', methods=['GET'])
def prediction_metrics():
    logs = load_logs()
    
    if not logs:  # Handle empty logs case
        return jsonify({"total_predictions": 0, "anomalies_detected": 0})
    
    total_predictions = len(logs)
    anomalies = sum(1 for log in logs if log.get("label") == 1)  # Use .get() to avoid KeyErrors

    return jsonify({
        "total_predictions": total_predictions,
        "anomalies_detected": anomalies
    })


if __name__ == "__main__":
    log_thread = Thread(target=consume_logs, daemon=True)
    log_thread.start()
    app.run(host="0.0.0.0", port=8500)
