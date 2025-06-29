# /ml/strategy_selector.py

import os
import pandas as pd
from datetime import datetime
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

TRADE_OUTCOME_LOG = "logs/trade_outcomes.csv"
MODEL_PATH = "models/strategy_selector_model.pkl"

# Add this model to your strategy router for smarter context-driven routing
# Future enhancements: replace with contextual bandits, policy gradient RL, or self-play sim results

def load_trade_data():
    if not os.path.exists(TRADE_OUTCOME_LOG):
        print("🚫 No trade outcome data found.")
        return pd.DataFrame()
    df = pd.read_csv(TRADE_OUTCOME_LOG, parse_dates=["entry_time", "exit_time"])
    df["hour"] = df["entry_time"].dt.hour
    df["dayofweek"] = df["entry_time"].dt.dayofweek
    df["target"] = (df["reward"] > 0).astype(int)  # profitable or not
    return df

def build_contextual_selector():
    df = load_trade_data()
    if df.empty:
        return
    if df['target'].nunique() < 2:
        print("⚠️ Not enough class diversity to train. Need both winners and losers.")
        return

    X = df[["strategy", "hour", "dayofweek"]]
    y = df["target"]

    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    X_encoded = encoder.fit_transform(X)

    if len(y) < 2:
        print("⚠️ Not enough samples to split. Training on full dataset.")
        X_train, y_train = X_encoded, y
        X_test, y_test = X_encoded, y
    else:
        X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42)
    if pd.Series(y_train).nunique() < 2:
        print("⚠️ y_train only contains one class after split. Training on full dataset.")
        X_train, y_train = X_encoded, y
        X_test, y_test = X_encoded, y

    model = LogisticRegression()
    try:
        model.fit(X_train, y_train)
    except ValueError as e:
        print(f"❌ Model training failed: {e}")
        return

    print("\n📊 Strategy Selector Performance:")
    print(classification_report(y_test, model.predict(X_test)))

    joblib.dump((model, encoder), MODEL_PATH)
    print(f"✅ Contextual model saved to {MODEL_PATH}")


def predict_success(strategy, hour, dayofweek):
    """Return the probability that a given strategy context will be profitable."""
    if not os.path.exists(MODEL_PATH):
        print("⚠️ No strategy selector model found.")
        return None

    model, encoder = joblib.load(MODEL_PATH)
    X = pd.DataFrame([{"strategy": strategy, "hour": hour, "dayofweek": dayofweek}])
    X_encoded = encoder.transform(X)
    prob = model.predict_proba(X_encoded)[0][1]  # probability of class 1 (profitable)
    return round(prob, 4)


if __name__ == "__main__":
    build_contextual_selector()
