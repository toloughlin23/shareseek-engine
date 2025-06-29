import os
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
import json
import pandas as pd

# Load API keys from environment or .env
load_dotenv()

ALPACA_API_KEY = os.getenv("APCA_API_KEY_ID")
ALPACA_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, BASE_URL)

st.set_page_config(page_title="Share-Seek Dashboard", layout="wide")

# Tabs
menu = st.sidebar.radio("📂 Navigation", ["Analytics", "Settings", "Backtesting", "ML Insights", "Paper Training", "Live Allocation"])

# Shared config path
strategy_state_path = "config.json"

strategy_list = [
    "ORB", "VWAP Reclaim", "Trend Continuation", "VWAP Slingshot",
    "Late-Day Reversal", "Sector Rotation", "Rolling Reversal",
    "Time-of-Day Bias", "High Volume Gap", "Pullback Resumption"
]

# --- SETTINGS TAB ---
if menu == "Settings":
    st.title("⚙️ Strategy Settings")
    if os.path.exists(strategy_state_path):
        with open(strategy_state_path, "r") as f:
            config = json.load(f)
    else:
        config = {"enabled": True, "strategies": {}}
        with open(strategy_state_path, "w") as f:
            json.dump(config, f)

    enabled = st.checkbox("Enable Strategy Engine", value=config.get("enabled", True))
    config["enabled"] = enabled
    st.markdown(f"**Status:** {'🟢 Enabled' if enabled else '🔴 Paused'}")

    st.subheader("📌 Per-Strategy Toggles")
    for strat in strategy_list:
        current = config["strategies"].get(strat, True)
        config["strategies"][strat] = st.checkbox(strat, value=current)

    with open(strategy_state_path, "w") as f:
        json.dump(config, f)

# --- ANALYTICS TAB ---
from polygon_stream import get_atr_snapshot
elif menu == "Analytics":
    st.title("📊 Account Analytics")
    try:
        account = api.get_account()
        col1, col2, col3 = st.columns(3)
        col1.metric("Equity", f"${float(account.equity):,.2f}")
        col2.metric("Buying Power", f"${float(account.buying_power):,.2f}")
        col3.metric("Daily P/L", f"${float(account.equity) - float(account.last_equity):,.2f}")
    except Exception as e:
        st.error(f"Account error: {e}")

    st.subheader("📡 Live ATR Snapshot")
    try:
        atr_data = get_atr_snapshot()
        atr_df = pd.DataFrame(list(atr_data.items()), columns=["Symbol", "ATR"])
        min_atr = st.number_input("Min ATR threshold (skip if above):", value=3.0, step=0.1)
        atr_df = atr_df[atr_df["ATR"] <= min_atr]
        st.dataframe(atr_df)
    except Exception as e:
        st.warning(f"Unable to load ATR snapshot: {e}")

    st.subheader("📌 Strategy P&L Summary")
    if os.path.exists("logs/backtest_signals.csv"):
        df = pd.read_csv("logs/backtest_signals.csv")
        grouped = df.groupby("strategy").agg({"pnl": "sum", "confidence": "mean"}).reset_index()
        grouped.columns = ["Strategy", "Total PnL", "Avg Confidence"]
        st.dataframe(grouped)

        st.subheader("📅 Per-Strategy Results")
        timeframe = st.selectbox("Select timeframe", ["Day", "Week"], key="analytics_timeframe")
        for strat in strategy_list:
            st.markdown(f"### 📈 {strat}")
            subset = df[df["strategy"] == strat].copy()
            if timeframe == "Day":
                cutoff = datetime.utcnow() - timedelta(days=1)
            else:
                cutoff = datetime.utcnow() - timedelta(days=7)
            if "timestamp" in subset.columns:
                subset["timestamp"] = pd.to_datetime(subset["timestamp"])
                filtered = subset[subset["timestamp"] > cutoff]
                if not filtered.empty:
                    st.dataframe(filtered[["symbol", "strategy", "direction", "entry", "final", "win", "pnl", "confidence"]])
                else:
                    st.info("No trades found for this period.")
            else:
                st.warning(f"⛔ 'timestamp' column missing for {strat}")

    st.subheader("📌 Open Positions")
    try:
        positions = api.list_positions()
        if not positions:
            st.info("No open positions.")
        else:
            for pos in positions:
                side = "🟢 LONG" if pos.side == "long" else "🔴 SHORT"
                unrealized = float(pos.unrealized_pl)
                color = "green" if unrealized >= 0 else "red"
                st.markdown(
                    f"**{pos.symbol}** — {side} | Qty: {pos.qty} | Avg Price: ${pos.avg_entry_price} | "
                    f"<span style='color:{color}'>Unrealized P/L: ${unrealized:.2f}</span>",
                    unsafe_allow_html=True
                )
    except Exception as e:
        st.error(f"Positions error: {e}")

# --- BACKTESTING TAB ---
elif menu == "Backtesting":
    st.title("🔁 Backtesting Results")
    if os.path.exists("logs/backtest_signals.csv"):
        df = pd.read_csv("logs/backtest_signals.csv")

        st.dataframe(df.tail(50))
        st.download_button("📥 Download Full Backtest Log", df.to_csv(index=False), file_name="backtest_signals.csv")

        st.subheader("📊 Strategy Summary")
        grouped = df.groupby("strategy").agg({"pnl": "sum", "confidence": "mean", "symbol": "count"}).reset_index()
        grouped.columns = ["Strategy", "Total PnL", "Avg Confidence", "Trade Count"]
        st.dataframe(grouped)

        st.subheader("📅 Per-Strategy Results")
        timeframe = st.selectbox("Select timeframe", ["Day", "Week"], key="backtest_timeframe")
        for strat in strategy_list:
            st.markdown(f"### 📈 {strat}")
            subset = df[df["strategy"] == strat].copy()
            if timeframe == "Day":
                cutoff = datetime.utcnow() - timedelta(days=1)
            else:
                cutoff = datetime.utcnow() - timedelta(days=7)
            if "timestamp" in subset.columns:
                subset["timestamp"] = pd.to_datetime(subset["timestamp"])
                filtered = subset[subset["timestamp"] > cutoff]
                if not filtered.empty:
                    st.dataframe(filtered[["symbol", "strategy", "direction", "entry", "final", "win", "pnl", "confidence"]])
                else:
                    st.info("No trades found for this period.")
            else:
                st.warning(f"⛔ 'timestamp' column missing for {strat}")
    else:
        st.warning("No backtest results found yet.")

# --- LIVE ALLOCATION TAB ---
    # Simulate live strategy toggles
    st.subheader("🧪 Live Strategy Toggle State")
    for name, rec in state.items():
        st.write(f"{name}: {'🟢 Live' if rec['enabled'] else '🔴 Disabled'}")
elif menu == "Live Allocation":
    from engine.allocation_manager import render_allocation_dashboard
    render_allocation_dashboard()

    # Display total capital usage
    from engine.allocation_manager import load_allocation_state
    state = load_allocation_state()
    total_pct = sum(rec['capital_pct'] for rec in state.values() if rec['enabled'])
    st.markdown(f"**🧮 Total Allocated Capital:** {total_pct:.1f}%")
    if total_pct > 100:
        st.error("⚠️ Capital allocation exceeds 100%! Adjust your strategy weights.")
    elif total_pct == 100:
        st.success("✅ Capital allocation is balanced at 100%.")
    else:
        st.info("ℹ️ You have unallocated capital remaining.")

# --- PAPER TRAINING TAB ---
elif menu == "Paper Training":
    from engine.promotion_manager import render_promotion_dashboard
    render_promotion_dashboard()

# --- ML SIGNAL SCORING TAB ---
elif menu == "ML Insights":
    st.title("🧠 ML Signal Scoring")
    from ml.signal_scorer import preview_scored_signals
    preview_scored_signals()

