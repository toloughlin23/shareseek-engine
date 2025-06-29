# /monitoring/system_health.py

import os
import json
import pandas as pd
from datetime import datetime, timedelta

MODEL_HISTORY_PATH = "ml/model_history.csv"
SIGNAL_LOG_PATH = "logs/signals.csv"
STALE_DAYS_THRESHOLD = 14


def check_model_freshness():
    if not os.path.exists(MODEL_HISTORY_PATH):
        return "⚠️ No model history found. Retraining may be needed."
    df = pd.read_csv(MODEL_HISTORY_PATH)
    if df.empty:
        return "⚠️ Model history is empty."
    last_timestamp = pd.to_datetime(df.iloc[-1]["timestamp"])
    age_days = (datetime.now() - last_timestamp).days
    if age_days > STALE_DAYS_THRESHOLD:
        return f"⚠️ Model is {age_days} days old. Consider retraining."
    return f"✅ Model is {age_days} days old. Fresh."


def summarize_rejection_reasons():
    if not os.path.exists(SIGNAL_LOG_PATH):
        return "No signals logged yet."
    df = pd.read_csv(SIGNAL_LOG_PATH, encoding='latin1', on_bad_lines='skip')
    if "status" not in df.columns or "reason" not in df.columns:
        return "Signal log missing rejection reason columns."
    rejections = df[df["status"] == "rejected"]
    if rejections.empty:
        return "✅ No rejected signals."
    return rejections["reason"].value_counts().to_dict()


# Add this data as a dashboard tab — show model freshness, rejection summary, and rejection rate.
def export_health_report():
    health = {
        "timestamp": datetime.now().isoformat(),
        "model_freshness": check_model_freshness(),
        "rejection_summary": summarize_rejection_reasons()
    }
    if isinstance(health["rejection_summary"], dict):
        total_signals = sum(health["rejection_summary"].values()) + 1
        health["rejection_rate"] = round(sum(health["rejection_summary"].values()) / total_signals, 4)
    else:
        health["rejection_rate"] = None

    os.makedirs("monitoring", exist_ok=True)
    with open("monitoring/system_health_report.json", "w") as f:
        json.dump(health, f, indent=2)
    print("📁 Health report exported to monitoring/system_health_report.json")


def send_slack_alert(message, webhook_url):
    try:
        import requests
        requests.post(webhook_url, json={"text": message})
    except Exception as e:
        print(f"⚠️ Slack alert failed: {e}")


# Include this function output in dashboard — refreshable model + signal health panel.
def check_system_health():
    export_health_report()
    print("🔍 Model Freshness:")
    print(check_model_freshness())
    print("\n📊 Rejection Reasons:")
    print(summarize_rejection_reasons())

    webhook_url = os.getenv("SLACK_WEBHOOK")
    if webhook_url:
        model_status = check_model_freshness()
        rejection_summary = summarize_rejection_reasons()
        if "⚠️" in model_status or (isinstance(rejection_summary, dict) and sum(rejection_summary.values()) > 10):
            alert_msg = (
                f"🚨 System Health Alert\n"
                f"Model: {model_status}\n"
                f"Rejections: {rejection_summary}"
            )
            send_slack_alert(alert_msg, webhook_url)


if __name__ == "__main__":
    check_system_health()
