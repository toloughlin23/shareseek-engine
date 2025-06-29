# /engine/regime_detector.py

def detect_regime(data):
    """
    Classifies the market regime using simple SMA comparison logic.
    Returns 'bull', 'bear', or 'sideways'.
    """
    if data['sma_20'][-1] > data['sma_50'][-1]:
        return 'bull'
    elif data['sma_20'][-1] < data['sma_50'][-1]:
        return 'bear'
    else:
        return 'sideways'
