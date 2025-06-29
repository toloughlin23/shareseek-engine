import pandas as pd
import logging

def gap_vwap_reclaim(df, symbol_meta):
    float_shares = symbol_meta.get("float", 1e8)
    min_float = 10_000_000
    if float_shares < min_float:
        return None, 0.0

    prev_close = symbol_meta.get("prev_close", df["close"].iloc[0] * 0.97)
    today_open = df["open"].iloc[0]
    gap_pct = (today_open - prev_close) / prev_close

    if gap_pct < 0.03:
        return None, 0.0

    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    df["vwap"] = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()

    if len(df) < 2:
        return None, 0.0

    bar2 = df.iloc[1]
    avg_vol = df["volume"].iloc[:2].mean()

    vwap_reclaim = bar2["close"] > bar2["vwap"]
    strong_volume = bar2["volume"] > avg_vol * 1.2

    if vwap_reclaim and strong_volume:
        confidence = min(1.0, bar2["volume"] / avg_vol)
        logging.info(f"Gap VWAP Reclaim signal @ {bar2['close']} conf={confidence:.2f}")
        return {"direction": "long", "entry": bar2["close"]}, confidence

    return None, 0.0
