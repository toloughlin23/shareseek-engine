# strategy_engine.py

# Note: This function assumes `health_tracker` is globally accessible.
# Consider integrating it into a shared class or controller module later to improve modularity.

import time
from datetime import datetime

# Shared storage from polygon_stream (could be imported or passed via multiprocessing/IPC)
live_prices = {}  # Should be linked to your actual live stream
news_feed = []    # Should be linked to live headline sentiment

# Symbol universe (subset based on filters)
SYMBOLS = ["AAPL", "MSFT", "GOOG"]  # Example set

# Import real strategy modules
from strategies.orb_breakout import run as orb_breakout_run
from strategies.vwap_slingshot import run as vwap_slingshot_run
from strategies.trend_continuation import run as trend_continuation_run
from strategies.gap_vwap_reclaim import run as gap_vwap_reclaim_run
from strategies.high_volume_gap import run as high_volume_gap_run
from strategies.late_day_reversal import run as late_day_reversal_run
from strategies.pullback_resumption import run as pullback_resumption_run
from strategies.rolling_reversal import run as rolling_reversal_run
from strategies.sector_rotation import run as sector_rotation_run
from strategies.tod_trend_bias import run as tod_trend_bias_run

# Real strategy map with optional parameter testing

def get_configurable_params():
    return {
        "threshold": [0.3, 0.5, 0.7],
        "risk_multiplier": [0.5, 0.75, 1.0]
    }

strategy_map = {
    "orb_breakout": orb_breakout_run,
    "vwap_slingshot": vwap_slingshot_run,
    "trend_continuation": trend_continuation_run,
    "gap_vwap_reclaim": gap_vwap_reclaim_run,
    "high_volume_gap": high_volume_gap_run,
    "late_day_reversal": late_day_reversal_run,
    "pullback_resumption": pullback_resumption_run,
    "rolling_reversal": rolling_reversal_run,
    "sector_rotation": sector_rotation_run,
    "tod_trend_bias": tod_trend_bias_run
}

# Example strategy configuration
RISK_THRESHOLD = 0.5  # Placeholder for minimum sentiment score to consider

# Load active strategy from JSON
import json

def get_active_strategy():
    try:
        with open("trading_state.json", "r") as f:
            return json.load(f).get("active_strategy", "default_strategy")
    except Exception:
        return "default_strategy"

# Toggle for live vs. paper mode
LIVE_MODE = True

# Position manager setup
from position_manager import PositionManager
pm = PositionManager()

# Placeholder for paper trades
ERROR_LOG = "logs/strategy_errors.csv"
import csv

FEEDBACK_LOG = "logs/strategy_feedback_log.csv"
executed_trades = []
health_tracker = {s: {"last_win": None, "total_trades": 0, "wins": 0, "pnl": 0, "paused": False} for s in strategy_map}

def strategy_loop():
    HEALTH_PNL_THRESHOLD = -500  # Trigger if net loss exceeds this
    HEALTH_WINRATE_THRESHOLD = 0.2  # Trigger if win rate falls below this
    AUTO_PAUSE = True  # Optional toggle to auto-pause strategies

    while True:
        # Check for resume request file
        try:
            with open("logs/resume_requests.json", "r") as f:
                request = json.load(f)
                strategy_to_resume = request.get("resume")
                if strategy_to_resume and strategy_to_resume in health_tracker:
                    health_tracker[strategy_to_resume]["paused"] = False
                    print(f"[▶️] Resume triggered: {strategy_to_resume}")
            # Clear the request file
            open("logs/resume_requests.json", "w").close()
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[resume check error] {e}")
        print("📌 Multi-strategy pass")
        try:
        with open("config/muted_symbols.json", "r") as f:
            muted_symbols = set(json.load(f).get("muted", []))
    except:
        muted_symbols = set()

    for symbol in SYMBOLS:
        if symbol in muted_symbols:
            print(f"[🚫] {symbol} is muted — skipping")
            continue
            try:
                with open("config/atr_config.json", "r") as cfg:
                    atr_threshold = json.load(cfg).get("atr_threshold", 3.0)
            except:
                atr_threshold = 3.0

            atr = live_prices.get(f"{symbol}_atr", 2.0)
            if atr > atr_threshold:
                print(f"[⛔] Skipping {symbol} — ATR {atr} exceeds threshold")
                with open("logs/skipped_due_to_atr.csv", "a", newline="") as skiplog:
                    writer = csv.DictWriter(skiplog, fieldnames=["timestamp", "symbol", "atr", "threshold"])
                    if skiplog.tell() == 0:
                        writer.writeheader()
                    writer.writerow({
                        "timestamp": datetime.utcnow().isoformat(),
                        "symbol": symbol,
                        "atr": atr,
                        "threshold": atr_threshold
                    })
                continue

            price = live_prices.get(symbol)
            if not price:
                continue

            recent_news = [n for n in news_feed if n['symbol'] == symbol]
            if recent_news:
                latest = recent_news[-1]
                sentiment = latest['score']
                headline = latest['headline']
            else:
                sentiment = 0
                headline = ""

            for strategy_name, strategy_fn in strategy_map.items():
                # Check health before running
                health = health_tracker[strategy_name]
                if AUTO_PAUSE:
                    if health["paused"]:
                        print(f"[⏸️] {strategy_name} is currently paused")
                        continue
                    if health["pnl"] < HEALTH_PNL_THRESHOLD or (health["total_trades"] >= 10 and (health["wins"] / health["total_trades"]) < HEALTH_WINRATE_THRESHOLD):
                        print(f"[⛔] Skipping {strategy_name} — flagged for underperformance")
                        health["paused"] = True
                        continue
                try:
                    signal = strategy_fn(symbol, price, sentiment, headline)
                    print(f"[INFO] Strategy '{strategy_name}' evaluated {symbol} @ {price:.2f} | Signal: {signal}")
                except Exception as e:
                    print(f"[ERROR] {strategy_name} on {symbol}: {e}")
                    with open(ERROR_LOG, "a", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=["timestamp", "strategy", "symbol", "error_message"])
                        if f.tell() == 0:
                            writer.writeheader()
                        writer.writerow({
                            "timestamp": datetime.utcnow().isoformat(),
                            "strategy": strategy_name,
                            "symbol": symbol,
                            "error_message": str(e)
                        })
                    continue

                if sentiment > RISK_THRESHOLD and signal:
                    atr = live_prices.get(f"{symbol}_atr", 2.0)  # Fallback to 2.0 if ATR not available
                    size = pm.compute_size(sentiment, atr)
                    stop = pm.set_stop(price, atr, side="long")
                    trade = {
                        "symbol": symbol,
                        "strategy": strategy_name,
                        "action": "BUY",
                        "price": price,
                        "sentiment": sentiment,
                        "headline": headline,
                        "confidence": sentiment,
                        "risk_multiplier": round(sentiment, 2),
                        "size": size,
                        "stop_loss": stop,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    executed_trades.append(trade)

                    strat_log_file = f"logs/{strategy_name}_log.csv"
                    with open(strat_log_file, "a", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=trade.keys())
                        if f.tell() == 0:
                            writer.writeheader()
                        writer.writerow(trade)

                    log_file = "logs/live_trades_log.csv" if LIVE_MODE else "logs/trades_log.csv"
                    with open(log_file, "a", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=trade.keys())
                        if f.tell() == 0:
                            writer.writeheader()
                        writer.writerow(trade)

                    print(f"[TRADE] {strategy_name}: {symbol} BUY @ {price:.2f} | Sentiment: {sentiment:.2f}")

                    # Strategy health update
                    health["total_trades"] += 1
                    health["wins"] += 1 if trade.get("pnl", 0) > 0 else 0
                    health["pnl"] += trade.get("pnl", 0)
                    if trade.get("pnl", 0) > 0:
                        health["last_win"] = datetime.utcnow().isoformat()

        time.sleep(60)  # Wait one minute between strategy passes

# Manual control panel for dashboard triggers
def resume_strategy(strategy_name):
    if strategy_name in strategy_map and health_tracker[strategy_name]["paused"]:
        health_tracker[strategy_name]["paused"] = False
        print(f"[▶️] {strategy_name} resumed by operator")


def list_paused_strategies():
    return [s for s, h in health_tracker.items() if h.get("paused")]

if __name__ == "__main__":
    print("🚀 Strategy engine running...")
    strategy_loop()
