# /ml/train_model.py

import pandas as pd
import os
import pickle
from sklearn.preprocessing import OrdinalEncoder
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import classification_report

INPUT_PATH = "ml/training_data.csv"
MODEL_OUTPUT_PATH = "models/ml_model.pkl"

CATEGORICAL_FEATURES = ["direction", "dna_tag", "regime"]
NUMERIC_FEATURES = ["rule_score", "regime_weight", "final_score", "risk_pct"]  # 'ml_score' removed to prevent leakage

def load_training_data(path=INPUT_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Training data not found at {path}")
    return pd.read_csv(path)

def preprocess(df):
    encoder = OrdinalEncoder()
    df[CATEGORICAL_FEATURES] = encoder.fit_transform(df[CATEGORICAL_FEATURES])
    X = df[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    y = df["label"]
    return X, y, encoder

def train_and_evaluate(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBClassifier(use_label_encoder=False, eval_metric="logloss")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    print("\n📊 Classification Report:\n")
    print(classification_report(y_test, y_pred))
    return model

def save_model(model, encoder):
    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    with open(MODEL_OUTPUT_PATH, "wb") as f:
        pickle.dump({"model": model, "encoder": encoder}, f)
    print(f"✅ Model and encoder saved to {MODEL_OUTPUT_PATH}")

# === Optional Add-Ons ===
# 📊 Feature importance dashboard → add SHAP or model.feature_importances_
# 🤖 Plug into live signal engine → score signals using trained model
# 📉 Drift detection → monitor changes in feature distributions
# 🧪 Model comparison → store evaluation reports per run
# 🔁 Auto-retraining → trigger when data exceeds a threshold row count

def run_training_pipeline():
    df = load_training_data()
    X, y, encoder = preprocess(df)
    model = train_and_evaluate(X, y)
    save_model(model, encoder)

if __name__ == "__main__":
    run_training_pipeline()
