import os
import pandas as pd
from strategies import ALL_STRATEGIES
from utils.logger import log_signal

# 🔧 Configurable Paths
DATA_DIR = "data/backtest_merged"  # Use merged historical data
RAW_DIR = "data/backtest_data"  # Where daily files are stored
MERGE_OUTPUT_DIR = DATA_DIR
BACKTEST_LOG = "logs/backtest_signals.csv"

SYMBOL_META = {
    "sector": "Technology",
    "float": 1e8,
    "catalyst": True,
    "spy_price": 425,
    "spy_ema50": 420
}

def merge_daily_data():
    print("🔄 Merging daily CSVs into full symbol datasets...")
    all_files = os.listdir(RAW_DIR)
    symbol_files = {}
    for f in all_files:
        if f.endswith(".csv") and "_" in f:
            sym = f.split("_")[0]
            symbol_files.setdefault(sym, []).append(f)

    os.makedirs(MERGE_OUTPUT_DIR, exist_ok=True)
    for symbol, files in symbol_files.items():
        combined = []
        for fname in sorted(files):
            df = pd.read_csv(os.path.join(RAW_DIR, fname))
            if "time" in df.columns and "timestamp" not in df.columns:
                df["timestamp"] = df["time"]
                df.drop(columns=["time"], inplace=True)
            if "timestamp" not in df.columns:
                continue
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
            combined.append(df)
        if combined:
            full_df = pd.concat(combined).drop_duplicates(subset="timestamp")
            full_df.sort_values("timestamp", inplace=True)
            full_df.to_csv(os.path.join(MERGE_OUTPUT_DIR, f"{symbol}.csv"), index=False)
            print(f"✅ Merged: {symbol} → {MERGE_OUTPUT_DIR}/{symbol}.csv")
        else:
            print(f"⚠️ No valid data for {symbol}")

def load_price_data(symbol):
    path = os.path.join(DATA_DIR, f"{symbol}.csv")
    if not os.path.exists(path):
        print(f"❌ Missing merged data file: {path}")
        return None

    df = pd.read_csv(path)
    print(f"📄 {symbol} columns: {df.columns.tolist()}")  # ✅ Debug output

    if "time" in df.columns and "timestamp" not in df.columns:
        df["timestamp"] = df["time"]
        df.drop(columns=["time"], inplace=True)

    if "timestamp" not in df.columns:
        print(f"⚠️ No timestamp column in {symbol} data")
        return None

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df.set_index("timestamp", inplace=True)

    df = df.apply(pd.to_numeric, errors="coerce")  # Ensure numeric types
    return df

def run_backtest():
    symbols = [f.replace(".csv", "") for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    all_logs = []

    for symbol in symbols:
        df = load_price_data(symbol)
        if df is None:
            continue

        print(f"\n🔍 Running backtest on {symbol} ({len(df)} rows)...")
        results = {}

        for strat_name, strategy_fn in ALL_STRATEGIES.items():
            try:
                signal, conf = strategy_fn(df.copy(), SYMBOL_META)
                if signal:
                    entry_price = signal["entry"]
                    last_close = df["close"].iloc[-1]
                    direction = signal["direction"]

                    win = (last_close > entry_price) if direction == "long" else (last_close < entry_price)
                    pnl = abs(last_close - entry_price) * (1 if win else -1)

                    log_signal(
                        strategy=strat_name,
                        symbol=symbol,
                        signal=direction,
                        confidence=conf,
                        price=entry_price,
                        sentiment_score=None
                    )

                    results[strat_name] = {
                        "direction": direction,
                        "entry": entry_price,
                        "final": last_close,
                        "win": win,
                        "pnl": round(pnl, 2),
                        "conf": round(conf, 2)
                    }

                    all_logs.append({
                        "symbol": symbol,
                        "strategy": strat_name,
                        "direction": direction,
                        "entry": entry_price,
                        "final": last_close,
                        "win": win,
                        "pnl": pnl,
                        "confidence": conf
                    })

                    print(f"✅ {symbol} | {strat_name} | {direction} @ {entry_price} | conf={conf:.2f}")
            except Exception as e:
                print(f"❌ {symbol} | {strat_name} error: {e}")

        if results:
            print("\n📊 Summary for", symbol)
            for strat, r in results.items():
                print(f"• {strat} | {'✅ Win' if r['win'] else '❌ Loss'} | P&L: {r['pnl']} | Conf: {r['conf']}")

    if all_logs:
        log_df = pd.DataFrame(all_logs)
        os.makedirs("logs", exist_ok=True)
        log_df.to_csv(BACKTEST_LOG, index=False)
        print(f"\n📝 Saved backtest log to {BACKTEST_LOG}")

if __name__ == "__main__":
    merge_daily_data()
    run_backtest()
