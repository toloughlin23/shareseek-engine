# /tests/test_strategy_router.py

from datetime import datetime
from engine.strategy_router import generate_trade_signal

# Mock input data for short and long timeframes
data_short = {
    'sma_20': [98, 99, 100, 101],
    'sma_50': [95, 96, 97, 98],
    'close': [102],
    'high': [100, 101, 102, 102],
    'low': [99, 98, 97, 97],
    'open': [100],
    'VWAP': [101],
    'volatility': [0.025]
}

data_long = {
    'sma_20': [390, 392, 395, 397],
    'sma_50': [388, 389, 390, 391]
}

symbol = 'AAPL'
now = datetime(2024, 6, 25, 9, 30)  # Morning session
test_volume = 1_500_000

signal = generate_trade_signal(data_short, data_long, symbol, now, test_volume, win_rate=0.65)

print("Test Signal Output:")
print(signal if signal else "Filtered (no trade)")
