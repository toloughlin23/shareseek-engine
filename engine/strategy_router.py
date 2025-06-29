# /engine/strategy_router.py

import csv
import os
from ml.strategy_selector import predict_success
from ml.live_model_scorer import score_signal
from datetime import datetime
from engine.dna_tagger import tag_dna
from engine.regime_detector import detect_regime
from engine.signal_filters import multi_timeframe_confirm, filter_by_time_and_volume
from engine.risk_engine import calculate_risk_pct

LOG_PATH = os.path.join("logs", "signals.csv")

def log_signal(signal, status="accepted"):
    os.makedirs("logs", exist_ok=True)
    signal_record = signal.copy()
    signal_record['status'] = status
    signal_record['timestamp'] = datetime.now().isoformat()
    signal_record['entry_price'] = None
    signal_record['exit_price'] = None
    signal_record['pnl'] = None

    fieldnames = list(signal_record.keys())
    file_exists = os.path.isfile(LOG_PATH)

    with open(LOG_PATH, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(signal_record)

def generate_trade_signal(data_short, data_long, symbol, now, avg_volume, win_rate=0.6):
    regime = detect_regime(data_long)

    if data_short['sma_20'][-1] > data_short['sma_50'][-1]:
        direction = 'long'
    elif data_short['sma_20'][-1] < data_short['sma_50'][-1]:
        direction = 'short'
    else:
        log_signal({'symbol': symbol, 'reason': 'no_crossover'}, status="rejected")
        return None

    strategy_name = 'crossover'

    temp_signal = {
        'symbol': symbol,
        'direction': direction,
        'rule_score': 0.7,
        'regime_weight': 0.9 if regime == 'bull' else 0.5,
        'final_score': 0.0,
        'dna_tag': tag_dna({'direction': direction}, data_short).replace('unclassified', 'other'),
        'regime': regime,
        'risk_pct': calculate_risk_pct(strategy_name, data_short['volatility'][-1], win_rate)
    }

    input_for_model = {
        'direction': temp_signal['direction'],
        'rule_score': temp_signal['rule_score'],
        'regime_weight': temp_signal['regime_weight'],
        'final_score': 0.0,
        'dna_tag': temp_signal['dna_tag'],
        'regime': temp_signal['regime'],
        'risk_pct': temp_signal['risk_pct']
    }

    temp_signal['ml_score'] = score_signal(input_for_model)
    temp_signal['final_score'] = round(sum([
        temp_signal['rule_score'],
        temp_signal['ml_score'],
        temp_signal['regime_weight']
    ]) / 3, 4)

    # Derive long-term direction for multi-timeframe filter
    if data_long['sma_20'][-1] > data_long['sma_50'][-1]:
        long_direction = 'long'
    elif data_long['sma_20'][-1] < data_long['sma_50'][-1]:
        long_direction = 'short'
    else:
        long_direction = None

    if not multi_timeframe_confirm(signal_short=temp_signal, signal_long={'symbol': symbol, 'direction': long_direction}):
        temp_signal['reason'] = 'timeframe_mismatch'
        log_signal(temp_signal, status="rejected")
        return None

    if not filter_by_time_and_volume(temp_signal, now, avg_volume):
        temp_signal['reason'] = 'time_volume_filter'
        log_signal(temp_signal, status="rejected")
        return None

    context_prob = predict_success(strategy_name, now.hour, now.weekday())
    temp_signal['context_score'] = context_prob
    if context_prob is not None and context_prob < 0.3:
        temp_signal['reason'] = 'context_model_filter'
        log_signal(temp_signal, status="rejected")
        return None

    signal = temp_signal
    signal['dna_tag'] = tag_dna(signal, data_short).replace('unclassified', 'other')
    signal['regime'] = regime
    signal['risk_pct'] = calculate_risk_pct(strategy_name, data_short['volatility'][-1], win_rate)

    log_signal(signal, status="accepted")
    return signal
