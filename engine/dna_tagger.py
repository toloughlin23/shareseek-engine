# /engine/dna_tagger.py

def tag_dna(signal, data):
    """
    Tag a trade signal with a behavior type for ML classification.
    Examples: 'breakout', 'VWAP curl', 'pullback', 'gap fill', etc.
    """
    if signal['direction'] == 'long':
        recent_high = max(data['high'][-10:-1])
        if data['close'][-1] > recent_high:
            return 'breakout'
        elif data['close'][-1] < data['VWAP'][-1]:
            return 'VWAP curl'
        elif data['low'][-1] < data['low'][-2] and data['close'][-1] > data['open'][-1]:
            return 'pullback'
    elif signal['direction'] == 'short':
        recent_low = min(data['low'][-10:-1])
        if data['close'][-1] < recent_low:
            return 'breakdown'
        elif data['close'][-1] > data['VWAP'][-1]:
            return 'VWAP fade'
        elif data['high'][-1] > data['high'][-2] and data['close'][-1] < data['open'][-1]:
            return 'fade'

    return 'unclassified'
