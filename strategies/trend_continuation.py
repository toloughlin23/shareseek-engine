import logging
import pandas as pd

def trend_continuation(df, symbol_meta):
    if symbol_meta.get("sector", "") not in ["Technology", "Finance", "Healthcare"]:
        return None, 0.0

    df["ema9"] = df["close"].ewm(span=9).mean()
    df["ema21"] = df["close"].ewm(span=21).mean()
    typical = (df["high"] + df["low"] + df["close"]) / 3
    df["vwap"] = (typical * df["volume"]).cumsum() / df["volume"].cumsum()

    spy_price = symbol_meta.get("spy_price", 420)
    spy_ema50 = symbol_meta.get("spy_ema50", 415)
    if spy_price < spy_ema50:
        return None, 0.0  # market not trending

    last_bar = df.iloc[-1]
    if (
        last_bar["close"] > last_bar["vwap"]
        and last_bar["ema9"] > last_bar["ema21"]
        and last_bar["volume"] > df["volume"].rolling(10).mean().iloc[-1] * 1.2
    ):
        conf = min(1.0, last_bar["volume"] / df["volume"].rolling(10).mean().iloc[-1])
        logging.info(f"Trend continuation signal at {last_bar['close']} conf {conf}")
        return {"direction": "long", "entry": last_bar["close"]}, conf

    return None, 0.0
