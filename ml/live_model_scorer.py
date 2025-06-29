# /ml/live_model_scorer.py

import pickle
import pandas as pd
from sklearn.preprocessing import OrdinalEncoder

MODEL_PATH = "models/ml_model.pkl"
CATEGORICAL_FEATURES = ["direction", "dna_tag", "regime"]
NUMERIC_FEATURES = ["rule_score", "regime_weight", "final_score", "risk_pct"]  # 'ml_score' removed — it's the prediction target

def load_model():
    with open(MODEL_PATH, "rb") as f:
        package = pickle.load(f)
    return package["model"], package["encoder"]

def prepare_input(signal_dict, encoder):
    df = pd.DataFrame([signal_dict])
    encoder.set_params(handle_unknown="use_encoded_value", unknown_value=-1)
    df[CATEGORICAL_FEATURES] = encoder.transform(df[CATEGORICAL_FEATURES])
    X = df[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    return X

def score_signal(signal_dict):
    model, encoder = load_model()
    X = prepare_input(signal_dict, encoder)
    prob = model.predict_proba(X)[0][1]  # probability of label = 1
    return round(prob, 4)

# Example usage:
if __name__ == "__main__":
    test_signal = {
        "direction": "long",
        "rule_score": 0.7,
        "ml_score": 0.65,
        "regime_weight": 0.9,
        "final_score": 0.75,
        "dna_tag": "breakout",
        "regime": "bull",
        "risk_pct": 0.01
    }
    print("ML Confidence Score:", score_signal(test_signal))
