import logging
import pandas as pd

def rolling_reversal(df, symbol_meta):
    if len(df) < 20:
        return None, 0.0

    df["change"] = df["close"].pct_change()
    df["rolling_std"] = df["change"].rolling(15).std()
    df["rolling_mean"] = df["close"].rolling(10).mean()

    recent = df.iloc[-1]
    mean = df["rolling_mean"].iloc[-1]

    if recent["close"] < mean and recent["rolling_std"] > 0.02:
        confidence = min(1.0, recent["rolling_std"] * 10)
        logging.info(f"Rolling Reversal Detected | Conf: {confidence}")
        return {"direction": "long", "entry": recent["close"]}, confidence

    return None, 0.0
