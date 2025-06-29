# /ml/prepare_training_data.py

import pandas as pd
import os
from datetime import datetime

INPUT_PATH = "logs/signals.csv"
OUTPUT_PATH = "ml/training_data.csv"

REQUIRED_FIELDS = [
    "symbol", "direction", "rule_score", "ml_score", "regime_weight",
    "final_score", "dna_tag", "regime", "risk_pct", "pnl", "status"
]

def load_signals(path=INPUT_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Signal log not found at {path}")
    df = pd.read_csv(path)
    return df

def clean_and_filter(df):
    df = df[df["status"] == "accepted"]
    df = df.dropna(subset=["final_score", "dna_tag", "regime"])
    df = df[df["final_score"] > 0]
    df = df[df["pnl"].notnull()]  # ensure only resolved trades
    return df[REQUIRED_FIELDS]

def create_labels(df):
    df["label"] = (df["pnl"] > 0).astype(int)  # 1 if profitable, else 0
    return df

def save_training_data(df, path=OUTPUT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"✅ Training data saved to {path} ({len(df)} rows)")

def track_training_growth(df):
    log_path = "ml/training_growth_log.csv"
    row = {
        "timestamp": datetime.now().isoformat(),
        "rows": len(df),
        "features": len(df.columns),
        "labels": df['label'].sum() if 'label' in df else 0
    }

    if os.path.exists(log_path):
        growth_log = pd.read_csv(log_path)
        growth_log = pd.concat([growth_log, pd.DataFrame([row])], ignore_index=True)
    else:
        growth_log = pd.DataFrame([row])

    growth_log.to_csv(log_path, index=False)
    print(f"📈 Growth tracked: {row['rows']} rows saved to log.")

def prepare_training_dataset():
    df = load_signals()
    df = clean_and_filter(df)
    df = create_labels(df)
    save_training_data(df)
    track_training_growth(df)

if __name__ == "__main__":
    prepare_training_dataset()
