# /engine/risk_engine.py

def calculate_risk_pct(strategy_name, volatility, win_rate):
    """
    Calculate dynamic risk percentage for position sizing.
    Uses strategy name, recent volatility, and win rate to adjust risk.
    """
    base_risk = 0.01  # default to 1% per trade

    # Volatility adjustment
    if volatility > 0.03:
        base_risk *= 0.8
    elif volatility < 0.01:
        base_risk *= 1.2

    # Win rate adjustment
    if win_rate < 0.5:
        base_risk *= 0.7
    elif win_rate > 0.65:
        base_risk *= 1.1

    return round(min(base_risk, 0.02), 4)  # cap at 2%
