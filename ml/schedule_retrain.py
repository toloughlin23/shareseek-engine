# /ml/schedule_retrain.py

import os
import pandas as pd
import subprocess
from datetime import datetime

GROWTH_LOG_PATH = "ml/training_growth_log.csv"
MODEL_HISTORY_PATH = "ml/model_history.csv"
MIN_NEW_ROWS = 500


def load_growth_log():
    if not os.path.exists(GROWTH_LOG_PATH):
        print("🚫 No training_growth_log.csv found.")
        return None
    return pd.read_csv(GROWTH_LOG_PATH)


def get_last_trained_rows():
    if not os.path.exists(MODEL_HISTORY_PATH):
        return 0
    df = pd.read_csv(MODEL_HISTORY_PATH)
    if df.empty:
        return 0
    return df.iloc[-1]["row_count"]


def snapshot_model():
    """Save a versioned snapshot of the latest model."""
    from shutil import copyfile
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    src = "models/ml_model.pkl"
    dst = f"models/ml_model_{timestamp}.pkl"
    if os.path.exists(src):
        copyfile(src, dst)
        print(f"📦 Snapshot saved: {dst}")
    else:
        print("⚠️ No base model found to snapshot.")


    os.makedirs(os.path.dirname(MODEL_HISTORY_PATH), exist_ok=True)
    log_row = {
        "timestamp": datetime.now().isoformat(),
        "row_count": row_count,
        "model_path": f"models/ml_model_{datetime.now().strftime('%Y%m%d_%H%M')}.pkl"
    }
    if os.path.exists(MODEL_HISTORY_PATH):
        df = pd.read_csv(MODEL_HISTORY_PATH)
        df = pd.concat([df, pd.DataFrame([log_row])], ignore_index=True)
    else:
        df = pd.DataFrame([log_row])
    df.to_csv(MODEL_HISTORY_PATH, index=False)
    print(f"🧠 Model retrained and logged: {log_row['model_path']}")


def check_and_retrain():
    growth_log = load_growth_log()
    if growth_log is None or growth_log.empty:
        return

    last_row_count = get_last_trained_rows()
    latest_row_count = growth_log.iloc[-1]["rows"]

    if latest_row_count - last_row_count >= MIN_NEW_ROWS:
        print(f"🔁 Retraining triggered: +{latest_row_count - last_row_count} new rows")
        subprocess.run(["python", "ml/train_model.py"])
        log_model_snapshot(latest_row_count)
        snapshot_model()
    else:
        print("✅ No retraining needed. Training data growth is below threshold.")


if __name__ == "__main__":
    check_and_retrain()
