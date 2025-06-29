# /engine/signal_filters.py

from datetime import datetime


def multi_timeframe_confirm(signal_short, signal_long):
    """
    Confirm that the signal aligns across multiple timeframes
    (e.g., short = 5m or 1h, long = daily).
    """
    return (
        signal_short['symbol'] == signal_long['symbol'] and
        signal_short['direction'] == signal_long['direction']
    )


def filter_by_time_and_volume(signal, now: datetime, avg_volume: float):
    """
    Filter signal based on time of day and average volume.
    - Trades only during opening and closing hour (9–10am, 3–4pm)
    - Requires minimum average volume of 1M
    """
    if now.hour not in range(9, 10) and now.hour not in range(15, 16):
        return False
    if avg_volume < 1_000_000:
        return False
    return True
