import os
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
import json

# Load API keys from environment or .env
load_dotenv()

ALPACA_API_KEY = os.getenv("APCA_API_KEY_ID")
ALPACA_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, BASE_URL)

st.set_page_config(page_title="Trading Dashboard", layout="wide")
st.title("📊 Trading Dashboard")

# Strategy Controls
st.sidebar.header("⚙️ Strategy Control")
strategy_state_path = "config.json"

# Load or initialize config
if os.path.exists(strategy_state_path):
    with open(strategy_state_path, "r") as f:
        config = json.load(f)
else:
    config = {"enabled": True}
    with open(strategy_state_path, "w") as f:
        json.dump(config, f)

enabled = st.sidebar.checkbox("Enable Strategy", value=config.get("enabled", True))
config["enabled"] = enabled

with open(strategy_state_path, "w") as f:
    json.dump(config, f)

st.sidebar.markdown(f"**Status:** {'🟢 Enabled' if enabled else '🔴 Paused'}")

# Account Info
st.header("📋 Account Overview")
try:
    account = api.get_account()
    col1, col2, col3 = st.columns(3)
    col1.metric("Equity", f"${float(account.equity):,.2f}")
    col2.metric("Buying Power", f"${float(account.buying_power):,.2f}")
    col3.metric("Daily P/L", f"${float(account.equity) - float(account.last_equity):,.2f}")
except Exception as e:
    st.error(f"Account error: {e}")

# Positions
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

# Orders this week
st.subheader("📅 Orders This Week")
start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
end = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

try:
    orders = api.list_orders(
        status='all',
        after=start,
        until=end,
        direction='desc'
    )

    total_profit = 0.0
    total_risk = 0.0
    filled_orders = []

    for order in orders:
        if order.filled_at:
            filled_orders.append(order)
            # Simplified P&L logic
            if order.side == "sell":
                total_profit += float(order.filled_avg_price or 0) * float(order.filled_qty or 0)
            elif order.side == "buy":
                total_risk += float(order.filled_avg_price or 0) * float(order.filled_qty or 0)

            submitted = order.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if order.submitted_at else "N/A"
            st.write(f"{order.side.upper()} {order.symbol} | Qty: {order.qty} | Status: {order.status} | Submitted: {submitted}")

    if filled_orders:
        ratio = (total_profit / total_risk) if total_risk > 0 else 0
        st.success(f"📈 Weekly P&L Est. (simplified): **${total_profit - total_risk:.2f}**")
        st.info(f"⚖️ Weekly Risk/Reward Ratio: **{ratio:.2f}**")
    else:
        st.info("No filled orders this week.")

except tradeapi.rest.APIError as e:
    st.error(f"Failed to fetch orders: {e}")

