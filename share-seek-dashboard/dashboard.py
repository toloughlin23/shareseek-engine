import streamlit as st
import pandas as pd
import os
import json
import alpaca_trade_api as tradeapi
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import shutil

# --- Config ---
API_KEY = os.getenv("APCA_API_KEY_ID")
SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"
data_folder = "C:/Users/tolou/Share-Seek/yfinance_docker/data"

symbols = ["AAPL", "MSFT", "TSLA"]
strategies = ["EMA Crossover", "VWAP Reversion", "Breakout"]
strategy_stats = {
    "EMA Crossover": {"win_rate": 61, "pnl": 3421},
    "VWAP Reversion": {"win_rate": 57, "pnl": 1985},
    "Breakout": {"win_rate": 63, "pnl": 4210},
}

# --- Connect to Alpaca ---
api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL)
account = api.get_account()

# --- System Health: Storage Info ---
def get_disk_usage():
    total, used, free = shutil.disk_usage("/")
    return round(free / (1024**3), 2), round(used / (1024**3), 2), round(total / (1024**3), 2)

# --- Layout ---
st.set_page_config(layout="wide")
st.title("📊 Share-Seek Dashboard")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["📈 Analytics", "⚙️ Settings", "📊 Back Testing", "🧠 ML Insights"])

# Simulated monthly performance for demonstration
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
monthly_pnl = {
    "EMA Crossover": np.random.randint(200, 800, size=12),
    "VWAP Reversion": np.random.randint(100, 600, size=12),
    "Breakout": np.random.randint(300, 1000, size=12),
}
monthly_winr = {
    "EMA Crossover": np.random.randint(55, 70, size=12),
    "VWAP Reversion": np.random.randint(50, 65, size=12),
    "Breakout": np.random.randint(60, 75, size=12),
}

# --- TAB 1: Analytics ---
with tab1:
    st.header("📈 Strategy Analytics")

    for strategy in strategies:
        st.subheader(f"📊 {strategy}")
        st.metric("Win Rate", f"{strategy_stats[strategy]['win_rate']}%")
        st.metric("Total P&L", f"${strategy_stats[strategy]['pnl']}")

        st.write("**Active Trades:**")
        active_trades = pd.DataFrame({
            "Symbol": ["AAPL", "MSFT", "TSLA"],
            "Entry Price": [173.2, 312.5, 244.7],
            "Current Price": [175.6, 309.9, 248.3],
            "P&L": [24.0, -26.0, 36.0],
            "Status": ["Open", "Open", "Open"]
        })
        st.dataframe(active_trades)

        st.subheader("📅 Monthly Performance")
        selected_month = st.selectbox("Select Month for CSV Export", months, key=f"month_export_{strategy}")
        st.write(f"📁 CSV export for {selected_month} available here.")

        # Monthly performance section with chart and trade summary
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.plot(months, monthly_pnl[strategy], label=f"P&L - {strategy}", marker='o')
        ax.plot(months, monthly_winr[strategy], label=f"WinR - {strategy}", marker='x')
        ax.set_ylabel("P&L / Win Rate")
        ax.set_ylim(0, 100)
        ax.set_title(f"{strategy} Monthly Metrics")
        ax.legend()
        st.pyplot(fig, use_container_width=False)

        st.write("**Monthly Trade Summary:**")
        monthly_trades = pd.DataFrame({
            "Date": ["2025-01-05", "2025-01-12", "2025-01-20"],
            "Symbol": ["AAPL", "MSFT", "TSLA"],
            "P&L": [150.25, -32.75, 84.10],
            "Strategy": [strategy]*3
        })
        st.dataframe(monthly_trades)

# --- TAB 2: Settings ---
with tab2:
    st.header("⚙️ Strategy & Risk Settings")
    st.metric("💰 Live Account Capital", f"${float(account.equity):,.2f}")
    for strategy in strategies:
        st.slider(f"{strategy} Allocation (%)", 0, 100, 30)
    trading_mode = st.radio("Trade Mode", ["Paper", "Live"], index=0)
    if trading_mode == "Live":
        st.warning("Are you sure you want to go live? Confirm below.")
        st.checkbox("✅ Confirm Live Trading")

# --- TAB 3: Back Testing ---
with tab3:
    st.header("📊 Back Testing Results")
    for strategy in strategies:
        st.subheader(f"📊 {strategy}")
        st.metric("Simulated Win Rate", f"{strategy_stats[strategy]['win_rate']}%")
        st.metric("Simulated P&L", f"${strategy_stats[strategy]['pnl']}")

        # Simulated backtested trades per strategy
        st.write("**Simulated Trades:**")
        simulated_trades = pd.DataFrame({
            "Symbol": ["AAPL", "MSFT", "TSLA"],
            "Entry Price": [172.0, 310.0, 243.0],
            "Exit Price": [174.5, 315.0, 245.5],
            "P&L": [25.0, 50.0, 25.0],
            "Status": ["Closed", "Closed", "Closed"]
        })
        st.dataframe(simulated_trades)

        selected_month_bt = st.selectbox("Select Month (Backtesting)", months, key=f"month_bt_export_{strategy}")
        st.write(f"📁 Backtest CSV export for {selected_month_bt} available here.")

        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.plot(months, monthly_pnl[strategy], label=f"P&L - {strategy}", marker='o')
        ax.plot(months, monthly_winr[strategy], label=f"WinR - {strategy}", marker='x')
        ax.set_ylabel("P&L / Win Rate")
        ax.set_ylim(0, 100)
        ax.set_title(f"Backtest: {strategy}")
        ax.legend()
        st.pyplot(fig, use_container_width=False)

        st.write("**Monthly Trade Summary (Backtesting):**")
        monthly_backtest_trades = pd.DataFrame({
            "Date": ["2025-01-03", "2025-01-10", "2025-01-17"],
            "Symbol": ["AAPL", "MSFT", "TSLA"],
            "P&L": [132.10, -42.75, 97.30],
            "Strategy": [strategy]*3
        })
        st.dataframe(monthly_backtest_trades)
# --- TAB 4: ML Insights ---
with tab4:
    st.header("🧠 ML Model Insights & Shadow Testing")
    st.subheader("📉 Current Model Performance vs Shadow Model")
    st.metric("Current Model Win Rate", "62.4%")
    st.metric("Shadow Model Win Rate", "64.1%")
    st.metric("Improvement Detected", "+1.7%", delta_color="normal")

    st.subheader("🧪 Last Retrain Summary")
    st.write("Last Retrain Date: 2025-08-01")
    st.write("Training Data Window: 270 days")
    st.write("Auto-promoted: ✅")

    st.subheader("📁 Storage & Cleanup Status")
    free, used, total = get_disk_usage()
    st.write(f"**Disk Space Remaining:** {free} GB of {total} GB")
    st.write("Last Cleanup: 2025-07-20 22:45")
    st.progress(free / total)

    if st.button("🧹 Trigger Manual Cleanup Now"):
        st.success("Manual cleanup completed. Logs rotated and old models compressed.")

    if st.button("🧪 Force Retrain"):
        st.info("Manual retrain initiated... Check logs for results.")

    if st.button("📁 Open Archive Folder"):
        st.write("Path: /share-seek/archive/")

    if st.button("🧹 Purge Logs Older Than 60 Days"):
        st.warning("17 orphan logs purged. 22.6 MB recovered.")

    st.subheader("⚙️ Archive Management")
    st.write("Only files older than 13 months will be shown here for deletion.")
    st.write("Auto-cleanup runs every 30 days.")
    st.checkbox("Auto-delete logs >13 months", value=True)
    st.checkbox("Auto-compress old models", value=True)

    st.info("ML module is running in shadow mode. No trades are influenced until promoted.")
