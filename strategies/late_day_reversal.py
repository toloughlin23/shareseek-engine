import logging
import pandas as pd

def late_day_reversal(df, symbol_meta):
    if df.index[-1].hour < 14:
        return None, 0.0  # Run after 2 PM only

    high_of_day = df["high"].max()
    recent_price = df["close"].iloc[-1]

    if recent_price < high_of_day * 0.985:
        confidence = 0.65
        logging.info(f"Late-day fade signal on reversal from HOD: {recent_price} (conf={confidence})")
        return {"direction": "short", "entry": recent_price}, confidence

    return None, 0.0
