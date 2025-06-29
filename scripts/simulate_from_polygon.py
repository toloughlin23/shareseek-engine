# /scripts/simulate_from_polygon.py (threaded version)

import time
import requests
import threading
from datetime import datetime
from engine.strategy_router import generate_trade_signal

API_KEY = "pMtj26Qxlt1SJhv8uOEAJ2rXwpE9EzzG"
SYMBOLS = ["AAPL", "MSFT", "TSLA"]
AVG_VOLUME = 1_500_000
POLL_INTERVAL = 60

URL_TEMPLATE = "https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?adjusted=true&apiKey={api_key}"


def fetch_latest_bar(symbol):
    url = URL_TEMPLATE.format(symbol=symbol, api_key=API_KEY)
    response = requests.get(url)
    if response.status_code != 200:
        print(f"[{symbol}] Failed to fetch bar: {response.status_code}")
        return None

    data = response.json()
    if "results" not in data or not data["results"]:
        return None

    bar = data["results"][0]
    return {
        "timestamp": datetime.fromtimestamp(bar["t"] / 1000.0),
        "open": bar["o"],
        "high": bar["h"],
        "low": bar["l"],
        "close": bar["c"],
        "volume": bar["v"]
    }


def build_sample_inputs(bar):
    return {
        "sma_20": [bar["close"]] * 20,
        "sma_50": [bar["close"] - 1.5] * 50,
        "volatility": [0.015] * 50,
        "close": [bar["close"]] * 20,
        "high": [bar["high"]] * 20,
        "VWAP": [bar["close"] - 0.5] * 20
    }


def simulate_symbol(symbol):
    while True:
        bar = fetch_latest_bar(symbol)
        if not bar:
            print(f"[{symbol}] No bar data. Skipping.")
            time.sleep(POLL_INTERVAL)
            continue

        now = datetime.now()
        data_short = build_sample_inputs(bar)
        data_long = build_sample_inputs(bar)

        signal = generate_trade_signal(data_short, data_long, symbol, now, bar["volume"], win_rate=0.65)
        if signal:
            print(f"✅ [{symbol}] Signal @ {now.strftime('%H:%M')} | Final: {signal['final_score']} | Context: {signal.get('context_score')}")
        else:
            print(f"⛔ [{symbol}] Signal rejected at {now.strftime('%H:%M')}")

        time.sleep(POLL_INTERVAL)


def simulate_all():
    for symbol in SYMBOLS:
        threading.Thread(target=simulate_symbol, args=(symbol,), daemon=True).start()
    while True:
        time.sleep(60)  # Keep main thread alive


if __name__ == "__main__":
    simulate_all()
