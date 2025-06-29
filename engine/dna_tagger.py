def tag_dna(signal_meta, data):
    """
    Classifies the signal into trade DNA patterns.
    Returns a string tag (e.g., 'reversal_bounce', 'breakout_pivot', etc.)
    Falls back to 'unclassified' or 'error:<msg>' if conditions aren't met.
    """
    try:
        required_cols = ['low', 'high', 'open', 'close']
        if not all(col in data for col in required_cols):
            return 'error:missing_columns'

        if len(data['low']) < 2 or len(data['close']) < 2 or len(data['open']) < 2:
            return 'error:insufficient_data'

        if data['low'][-1] < data['low'][-2] and data['close'][-1] > data['open'][-1]:
            return 'reversal_bounce'

        if data['high'][-1] > max(data['high'][-5:-1]):
            return 'breakout_pivot'

        return 'unclassified'

    except Exception as e:
        return f'error:{str(e)}'
