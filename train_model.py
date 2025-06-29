import pandas as pd
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

LOG_PATH = "logs/backtest_signals.csv"
MODEL_PATH = "models/ml_model.pkl"

def train_model():
    if not os.path.exists(LOG_PATH):
        print(f"❌ Cannot find backtest log at {LOG_PATH}")
        return

    df = pd.read_csv(LOG_PATH)
    print(f"✅ Loaded {len(df)} rows from backtest log.")

    if "win" not in df.columns:
        print("❌ 'win' column is missing from logs.")
        return

    df.dropna(subset=["confidence", "pnl"], inplace=True)

    # Convert categorical data
    df["strategy"] = df["strategy"].astype("category").cat.codes
    df["symbol"] = df["symbol"].astype("category").cat.codes

    X = df[["strategy", "symbol", "confidence", "pnl"]]
    y = df["win"].astype(int)

    if y.value_counts().min() < 2:
        print("❌ Not enough win/loss data to train (need both classes).")
        return

    X_train, X_val, y_train, y_val = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_val)
    acc = accuracy_score(y_val, preds)
    print(f"✅ Model accuracy: {acc*100:.2f}%")

    os.makedirs("models", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"📦 Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
