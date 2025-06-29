import logging
import pandas as pd

def high_volume_gap(df, symbol_meta):
    if df.empty or len(df) < 2:
        return None, 0.0

    day_open = df["open"].iloc[0]
    prev_close = symbol_meta.get("prev_close", day_open * 0.98)
    gap_pct = (day_open - prev_close) / prev_close

    avg_volume = df["volume"].rolling(5).mean().iloc[0]
    current_volume = df["volume"].iloc[0]

    if gap_pct > 0.03 and current_volume > avg_volume * 1.5:
        logging.info(f"Gap with high volume detected. Open: {day_open}, Gap: {gap_pct:.2%}")
        return {"direction": "long", "entry": day_open}, min(1.0, gap_pct * 30)

    return None, 0.0
