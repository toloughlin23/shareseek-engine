# /logs/log_trade_outcome.py

import os
import csv
from datetime import datetime

TRADE_OUTCOME_LOG = "logs/trade_outcomes.csv"

FIELDNAMES = [
    "symbol", "strategy", "entry_time", "exit_time", "entry_price",
    "exit_price", "pnl", "hold_time_minutes", "reward"
]

def log_trade_outcome(symbol, strategy, entry_time, exit_time, entry_price, exit_price):
    pnl = round(exit_price - entry_price, 4)
    hold_time_minutes = round((exit_time - entry_time).total_seconds() / 60, 2)
    reward = round(pnl / entry_price, 4)  # normalized reward

    log_entry = {
        "symbol": symbol,
        "strategy": strategy,
        "entry_time": entry_time.isoformat(),
        "exit_time": exit_time.isoformat(),
        "entry_price": entry_price,
        "exit_price": exit_price,
        "pnl": pnl,
        "hold_time_minutes": hold_time_minutes,
        "reward": reward
    }

    os.makedirs(os.path.dirname(TRADE_OUTCOME_LOG), exist_ok=True)
    file_exists = os.path.isfile(TRADE_OUTCOME_LOG)

    with open(TRADE_OUTCOME_LOG, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(log_entry)

    print(f"📈 Trade outcome logged: {log_entry}")

# Example usage:
if __name__ == "__main__":
    log_trade_outcome(
        symbol="AAPL",
        strategy="breakout",
        entry_time=datetime(2025, 6, 27, 10, 15),
        exit_time=datetime(2025, 6, 27, 14, 45),
        entry_price=125.50,
        exit_price=130.25
    )
