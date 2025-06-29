import logging
import pandas as pd

def vwap_slingshot(df, symbol_meta):
    if not symbol_meta.get("catalyst", True):
        return None, 0.0

    df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3
    df["vwap"] = (df["typical_price"] * df["volume"]).cumsum() / df["volume"].cumsum()

    last_bar = df.iloc[-1]
    if (
        last_bar["close"] < last_bar["vwap"] and
        last_bar["close"] > df["low"].rolling(20).min().iloc[-1]
    ):
        conf = 0.7
        logging.info(f"VWAP slingshot reversion signal: {last_bar['close']} (conf: {conf})")
        return {"direction": "long", "entry": last_bar["close"]}, conf

    return None, 0.0
