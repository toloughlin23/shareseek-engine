import logging
import pandas as pd

def pullback_resumption(df, symbol_meta):
    if len(df) < 30:
        return None, 0.0

    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema9"] = df["close"].ewm(span=9).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if (
        last["close"] > last["ema20"]
        and prev["close"] < prev["ema9"]
        and last["close"] > prev["close"]
    ):
        logging.info(f"Pullback resumption detected at {last.name} @ {last['close']}")
        return {"direction": "long", "entry": last["close"]}, 0.72

    return None, 0.0
