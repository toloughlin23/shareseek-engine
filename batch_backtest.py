import os
import pandas as pd
import logging
from strategies import ALL_STRATEGIES
from utils.logger import log_signal

logging.basicConfig(level=logging.INFO)
data_path = "data/backtest_data"

symbol_meta = {
    "sector": "Technology",
    "float": 100_000_000,
    "catalyst": True,
    "spy_price": 425,
    "spy_ema50": 420
}

def run_batch_backtest():
    for filename in os.listdir(data_path):
        if not filename.endswith(".csv"):
            continue

        symbol = filename.replace(".csv", "")
        df = pd.read_csv(os.path.join(data_path, filename))
        if "time" not in df.columns:
            logging.warning(f"{symbol} missing 'time' column")
            continue

        df["time"] = pd.to_datetime(df["time"])

        for strat_name, strat_fn in ALL_STRATEGIES.items():
            try:
                signal, conf = strat_fn(df.copy(), symbol_meta)
                if signal:
                    log_signal(
                        strategy=strat_name,
                        symbol=symbol,
                        signal=signal["direction"],
                        confidence=conf,
                        price=signal["entry"]
                    )
                    logging.info(f"{symbol} | {strat_name} → {signal['direction']} @ {signal['entry']} (conf={conf:.2f})")
            except Exception as e:
                logging.error(f"[{symbol}] {strat_name} failed: {e}")

if __name__ == "__main__":
    run_batch_backtest()
