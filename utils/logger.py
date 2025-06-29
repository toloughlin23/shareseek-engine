import csv
from datetime import datetime
import os

def log_signal(strategy, symbol, signal, confidence, price, sentiment_score=None):
    log_path = "data/signals_log.csv"
    file_exists = os.path.isfile(log_path)

    with open(log_path, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "symbol", "strategy", "signal", "confidence", "price", "sentiment_score"])

        writer.writerow([
            datetime.utcnow().isoformat(),
            symbol,
            strategy,
            signal,
            round(confidence, 4),
            round(price, 2),
            round(sentiment_score, 3) if sentiment_score is not None else ""
        ])
