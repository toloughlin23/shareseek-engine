# signal_scorer.py

import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import shap
import os

# Load trained model
MODEL_PATH = "models/ml_model.pkl"
model = joblib.load(MODEL_PATH)

# Load and prepare input features
INPUT_PATH = "data/ml_pretreaning_data/input_signals.csv"  # Change as needed
OUTPUT_LOG = "logs/scored_signals.csv"

# Load the input signal data
df = pd.read_csv(INPUT_PATH)

# Assume last N columns are features
feature_cols = [col for col in df.columns if col not in ["symbol", "timestamp"]]

# Standardize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[feature_cols])

# Predict signal scores
df["confidence"] = model.predict_proba(X_scaled)[:, 1]  # Assuming binary classifier

# SHAP value computation
explainer = shap.Explainer(model, X_scaled)
shap_values = explainer(X_scaled)
shap.summary_plot(shap_values, df[feature_cols], show=False)
shap_output_path = "logs/shap_summary.png"

if not os.path.exists("logs"):
    os.makedirs("logs")

print(f"Saving SHAP summary to: {shap_output_path}")
shap.plots.save(shap_output_path)

# Save results to log file
df[["symbol", "timestamp", "confidence"] + feature_cols].to_csv(OUTPUT_LOG, index=False)
print(f"✅ Signals scored and logged to {OUTPUT_LOG}")
