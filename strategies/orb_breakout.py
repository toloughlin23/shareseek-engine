import pandas as pd
import logging

def orb_breakout(df, symbol_meta):
    try:
        # Filter out low-float or no-catalyst stocks
        if not symbol_meta.get("catalyst", True) or symbol_meta.get("float", 1e9) < 10_000_000:
            return None, 0.0

        df = df.copy()

        # Ensure timestamp is datetime and use it as index if not already
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
            df = df.dropna(subset=["timestamp"])
            df = df.set_index("timestamp")

        if not isinstance(df.index, pd.DatetimeIndex):
            logging.warning("[ORB ERROR] Index is not datetime")
            return None, 0.0

        # Filter to opening range
        df = df.between_time("09:30", "10:30")

        if df.empty:
            return None, 0.0

        # Compute range and volume baseline
        range_high = df["high"].max()
        range_low = df["low"].min()
        avg_vol = df["volume"].mean()
        latest = df.iloc[-1]

        # Breakout or breakdown
        if latest["close"] > range_high and latest["volume"] > avg_vol * 1.5:
            conf = min(1.0, latest["volume"] / avg_vol)
            logging.info(f"[ORB] Breakout long at {latest['close']} conf={conf:.2f}")
            return {"direction": "long", "entry": latest["close"]}, conf

        if latest["close"] < range_low and latest["volume"] > avg_vol * 1.5:
            conf = min(1.0, latest["volume"] / avg_vol)
            logging.info(f"[ORB] Breakdown short at {latest['close']} conf={conf:.2f}")
            return {"direction": "short", "entry": latest["close"]}, conf

        return None, 0.0

    except Exception as e:
        logging.warning(f"[ORB ERROR] {e}")
        return None, 0.0
