
# /tests/test_signal.py

from datetime import datetime
from engine.strategy_router import generate_trade_signal

# Simulated short-term and long-term data frames
data_short = {
    'sma_20': [101, 102, 103, 104],
    'sma_50': [100, 100, 100, 100],
    'close': [104],
    'high': [103, 104, 105, 106],
    'low': [100, 101, 102, 103],
    'open': [102],
    'VWAP': [103],
    'volatility': [0.02]
}

data_long = {
    'sma_20': [390, 400, 410, 420],
    'sma_50': [380, 390, 400, 410]
}

symbol = "AAPL"
now = datetime(2025, 6, 25, 9, 45)
avg_volume = 1_250_000

signal = generate_trade_signal(data_short, data_long, symbol, now, avg_volume, win_rate=0.65)

print("\n🚀 Test Live Signal Output with ML Scoring:\n")
print(signal if signal else "Signal was rejected by filters.")
