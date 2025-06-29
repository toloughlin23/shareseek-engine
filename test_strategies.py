from strategies import ALL_STRATEGIES
import pandas as pd

# Dummy data for testing
df = pd.DataFrame({
    "open": [100] * 60,
    "high": [105] * 60,
    "low": [95] * 60,
    "close": [100 + (i % 5) for i in range(60)],
    "volume": [1_000_000] * 60
})
prev_close = 98
symbol_meta = {"sector": "Technology", "spy_price": 422, "spy_ema50": 420}

for name, fn in ALL_STRATEGIES.items():
    try:
        if name == "VWAP Reclaim":
            signal, conf = fn(df, prev_close)
        elif name == "Trend Continuation":
            signal, conf = fn(df, pd.DataFrame(df))  # reuse dummy df for SPY
        else:
            signal, conf = fn(df)
        print(f"{name}: Signal={signal}, Confidence={conf}")
    except Exception as e:
        print(f"{name}: ⚠️ Error - {e}")
