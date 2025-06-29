# /engine/promotion_manager.py

import json
import os
from datetime import datetime, timedelta
import streamlit as st  # Dashboard hook

# Plan to add a dashboard view to visualize this file — schedule a hook in Phase 2.1 for a [Paper Symbol Review Tab] that reads from symbol_status.json
PROMOTION_FILE = os.path.join("state", "symbol_status.json")

DEFAULT_SYMBOL_RECORD = {
    "mode": "paper",
    "trades": 0,
    "wins": 0,
    "losses": 0,
    "last_promotion_check": None,
    "blocked": False,
    "cooldown": False
}

PROMOTION_CRITERIA = {
    "min_trades": 10,
    "min_win_rate": 0.55
}

def load_symbol_status():
    if not os.path.exists(PROMOTION_FILE):
        return {}
    with open(PROMOTION_FILE, 'r') as f:
        return json.load(f)

def save_symbol_status(status):
    os.makedirs(os.path.dirname(PROMOTION_FILE), exist_ok=True)
    with open(PROMOTION_FILE, 'w') as f:
        json.dump(status, f, indent=2)

def update_symbol(symbol, result):
    status = load_symbol_status()
    record = status.get(symbol, DEFAULT_SYMBOL_RECORD.copy())

    record["trades"] += 1
    if result == "win":
        record["wins"] += 1
    elif result == "loss":
        record["losses"] += 1

    record["last_promotion_check"] = datetime.now().isoformat()
    status[symbol] = record
    save_symbol_status(status)

def evaluate_promotion(symbol):
    status = load_symbol_status()
    record = status.get(symbol)
    if not record or record["mode"] != "paper" or record.get("blocked"):
        return False

    if record["trades"] >= PROMOTION_CRITERIA["min_trades"]:
        win_rate = record["wins"] / record["trades"]
        if win_rate >= PROMOTION_CRITERIA["min_win_rate"]:
            record["mode"] = "live"
            status[symbol] = record
            save_symbol_status(status)
            return True
    return False

def set_symbol_mode(symbol, mode):
    status = load_symbol_status()
    if symbol in status:
        status[symbol]["mode"] = mode
        if mode == "blocked":
            status[symbol]["blocked"] = True
        save_symbol_status(status)

def render_promotion_dashboard():
    st.title("🧪 Paper Symbol Review")
    status = load_symbol_status()

    if not status:
        st.info("No symbols being tracked yet.")
        return

    rows = []
    for sym, rec in status.items():
        total = rec["trades"]
        wins = rec["wins"]
        win_rate = wins / total if total else 0
        mode = rec.get("mode", "paper")
        reason = ""
        if mode == "paper" and total < PROMOTION_CRITERIA["min_trades"]:
            reason = f"Needs {PROMOTION_CRITERIA['min_trades'] - total} more trades"
        elif mode == "paper" and win_rate < PROMOTION_CRITERIA["min_win_rate"]:
            reason = "Win rate too low"

        rows.append({
            "Symbol": sym,
            "Mode": mode,
            "Trades": total,
            "Wins": wins,
            "Losses": rec["losses"],
            "Win Rate": f"{win_rate:.2%}",
            "Last Check": rec["last_promotion_check"],
            "Reason": reason
        })

    st.dataframe(rows)

    st.subheader("📍 Manual Promotion & Block Controls")
    symbol_input = st.text_input("Symbol to manage:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Promote to Live") and symbol_input:
            set_symbol_mode(symbol_input, "live")
            st.success(f"{symbol_input} promoted to live mode.")
    with col2:
        if st.button("Block Symbol") and symbol_input:
            set_symbol_mode(symbol_input, "blocked")
            st.warning(f"{symbol_input} has been blocked.")
