 
import logging
import pandas as pd

def tod_trend_bias(df, symbol_meta):
    if len(df) < 30:
        return None, 0.0

    hour = pd.to_datetime(df.index[-1]).hour
    if 9 <= hour <= 10 or 14 <= hour <= 15:
        logging.info(f"Time-of-day trend bias active at {df.index[-1]}")
        return {"direction": "long", "entry": df['close'].iloc[-1]}, 0.66

    return None, 0.0
