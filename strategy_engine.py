
import os
import json
import time
import requests
from datetime import datetime, timedelta
import pandas as pd
import alpaca_trade_api as tradeapi

# === Load config ===
CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

API_KEY = os.getenv("APCA_API_KEY_ID")
SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"
WEBHOOK_URL = "http://127.0.0.1:5001/webhook"
WEBHOOK_KEY = "PKG7KD1YOVP9GXEHSWB9"

api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL)

log_file = "trade_log.txt"
placed_orders = set()

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(log_file, "a") as f:
        f.write(line + "\n")

def send_webhook(symbol, strategy, action):
    payload = {
        "key": WEBHOOK_KEY,
        "strategy": strategy,
        "symbol": symbol,
        "action": action
    }
    try:
        r = requests.post(WEBHOOK_URL, json=payload)
        log(f"Webhook response for {symbol}: {r.status_code} - {r.text}")
    except Exception as e:
        log(f"Error sending webhook: {e}")

def get_ema_crossover_signal(symbol):
    log(f"[EMA] Checking {symbol}...")
    try:
        end = datetime.now()
        start = end - timedelta(days=100)
        bars = api.get_bars(symbol, tradeapi.TimeFrame.Day, start=start.date().isoformat(), end=end.date().isoformat()).df
        if bars.empty or len(bars) < 50:
            log(f"[EMA] ❌ Not enough data for {symbol}")
            return False

        bars["EMA20"] = bars["close"].ewm(span=20).mean()
        bars["EMA50"] = bars["close"].ewm(span=50).mean()

        if bars["EMA20"].iloc[-2] < bars["EMA50"].iloc[-2] and bars["EMA20"].iloc[-1] > bars["EMA50"].iloc[-1]:
            log(f"[SIGNAL] ✅ EMA crossover for {symbol}")
            return True
    except Exception as e:
        log(f"[ERROR] Fetching bars for {symbol}: {e}")
    return False

def run_strategy_engine():
    log("\n=== Running Strategy Engine ===")
    strategies = config.get("strategies", {})

    for name, settings in strategies.items():
        if not settings.get("enabled") or settings.get("paused"):
            continue

        for symbol in settings.get("symbols", []):
            key = f"{name}_{symbol}"
            if key in placed_orders:
                continue

            log(f"[INFO] Checking signal for {symbol}")
            signal = False

            if name == "EMA Crossover":
                signal = get_ema_crossover_signal(symbol)

            if signal:
                send_webhook(symbol, name, "buy")
                placed_orders.add(key)
            else:
                log(f"[INFO] No signal for {symbol}")

    log("\n[WAIT] Sleeping for 5 minutes...\n")

if __name__ == "__main__":
    while True:
        run_strategy_engine()
        time.sleep(300)  # Wait 5 minutes
