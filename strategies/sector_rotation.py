import logging
import pandas as pd

def sector_rotation(df, symbol_meta):
    if symbol_meta.get("sector") not in ["Technology", "Financial", "Healthcare"]:
        return None, 0.0

    df["return"] = df["close"].pct_change()
    df["rolling_strength"] = df["return"].rolling(15).mean()

    last_strength = df["rolling_strength"].iloc[-1]
    if last_strength > 0.002:
        confidence = min(1.0, last_strength * 100)
        logging.info(f"Sector momentum signal: conf={confidence:.2f}")
        return {"direction": "long", "entry": df['close'].iloc[-1]}, confidence

    return None, 0.0
