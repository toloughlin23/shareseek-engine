# /engine/allocation_manager.py

import json
import os
import streamlit as st

ALLOCATION_FILE = os.path.join("state", "allocation_state.json")

DEFAULT_STRATEGY_ALLOCATION = {
    "strategy": "",
    "enabled": True,
    "capital_pct": 10,  # default 10% allocation
    "risk_pct": 1.0,    # default 1% per trade
    "last_updated": None
}

def load_allocation_state():
    if not os.path.exists(ALLOCATION_FILE):
        return {}
    with open(ALLOCATION_FILE, 'r') as f:
        return json.load(f)

def save_allocation_state(data):
    os.makedirs(os.path.dirname(ALLOCATION_FILE), exist_ok=True)
    with open(ALLOCATION_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def update_strategy_allocation(strategy_name, capital_pct=None, risk_pct=None, enabled=None):
    state = load_allocation_state()
    record = state.get(strategy_name, DEFAULT_STRATEGY_ALLOCATION.copy())
    record["strategy"] = strategy_name

    if capital_pct is not None:
        record["capital_pct"] = capital_pct
    if risk_pct is not None:
        record["risk_pct"] = risk_pct
    if enabled is not None:
        record["enabled"] = enabled

    from datetime import datetime
    record["last_updated"] = datetime.now().isoformat()
    state[strategy_name] = record
    save_allocation_state(state)

def render_allocation_dashboard():
    st.title("📊 Strategy Allocation Manager")
    state = load_allocation_state()

    if not state:
        st.info("No strategy allocation records found.")
        return

    for name, rec in state.items():
        st.subheader(f"🧠 {name}")
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            capital = st.slider(f"Capital % for {name}", 0, 100, rec["capital_pct"], key=f"cap_{name}")
        with col2:
            risk = st.slider(f"Risk % for {name}", 0.0, 5.0, rec["risk_pct"], step=0.1, key=f"risk_{name}")
        with col3:
            toggle = st.checkbox("Enabled", value=rec["enabled"], key=f"enable_{name}")

        if st.button(f"💾 Save {name}"):
            update_strategy_allocation(name, capital, risk, toggle)
            st.success(f"Updated allocation for {name}")
