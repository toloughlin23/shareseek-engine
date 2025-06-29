import logging
import pandas as pd

from .orb_breakout import orb_breakout
from .gap_vwap_reclaim import gap_vwap_reclaim
from .trend_continuation import trend_continuation
from .vwap_slingshot import vwap_slingshot
from .late_day_reversal import late_day_reversal
from .sector_rotation import sector_rotation
from .rolling_reversal import rolling_reversal
from .tod_trend_bias import tod_trend_bias
from .high_volume_gap import high_volume_gap
from .pullback_resumption import pullback_resumption

ALL_STRATEGIES = {
    "ORB": orb_breakout,
    "VWAP Reclaim": gap_vwap_reclaim,
    "Trend Continuation": trend_continuation,
    "VWAP Slingshot": vwap_slingshot,
    "Late-Day Reversal": late_day_reversal,
    "Sector Rotation": sector_rotation,
    "Rolling Reversal": rolling_reversal,
    "Time-of-Day Bias": tod_trend_bias,
    "High Volume Gap": high_volume_gap,
    "Pullback Resumption": pullback_resumption,
}
