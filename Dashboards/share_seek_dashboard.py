# share_seek_dashboard.py

import streamlit as st
import pandas as pd
import os
import csv
from datetime import datetime

st.set_page_config(page_title="Share-Seek Unified Dashboard", layout="wide")
st.title("📊 Share-Seek Control Center")

# Navigation tabs
view = st.sidebar.radio("Select View:", ["Resume Strategies", "ML Dashboard", "Live Signal Queue", "Strategy Errors", "Backtesting Results", "Live", "Model Trainer"])

# --- ML Dashboard ---
if view == "ML Dashboard":
    st.header("🧠 ML Dashboard")

    METRICS_LOG = "logs/training_metrics.csv"
    TRAIN_SCRIPT = "ml/train_model.py"
    MODELS_DIR = "models/"
    DATA_UPLOAD_PATH = "data/ml_pretreaning_data/input_signals.csv"

    # Upload new data
    st.subheader("📤 Upload Input Signals")
    uploaded_file = st.file_uploader("Upload input_signals.csv", type="csv")
    if uploaded_file:
        with open(DATA_UPLOAD_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("✅ New training data uploaded successfully.")

    # Model selection
    st.subheader("🧠 Select Trained Model")
    models = [f for f in os.listdir(MODELS_DIR) if f.endswith(".pkl")]
    selected_model = st.selectbox("Available models:", models) if models else None

    # Training controls
    st.subheader("🚀 Manual Retrain")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Run Fast Retrain"):
            result = os.popen(f"python {TRAIN_SCRIPT} --fast").read()
            st.code(result)
    with col2:
        if st.button("Run Full Retrain"):
            result = os.popen(f"python {TRAIN_SCRIPT}").read()
            st.code(result)

    # Metrics and trends
    st.subheader("📈 Training Metrics")
    if os.path.exists(METRICS_LOG):
        df_metrics = pd.read_csv(METRICS_LOG)
        st.dataframe(df_metrics)
        df_metrics["timestamp"] = pd.to_datetime(df_metrics["timestamp"], errors="coerce")
        st.line_chart(df_metrics.set_index("timestamp")["accuracy"])
    else:
        st.info("No training metrics found.")

    # Live scoring and SHAP (if model and data uploaded)
    if selected_model and uploaded_file:
        import joblib
        from sklearn.preprocessing import StandardScaler
        import shap
        import matplotlib.pyplot as plt

        st.subheader("🔍 Model Scoring Preview")
        df_signals = pd.read_csv(DATA_UPLOAD_PATH)
        feature_cols = [col for col in df_signals.columns if col not in ["symbol", "timestamp"]]
        model = joblib.load(os.path.join(MODELS_DIR, selected_model))
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_signals[feature_cols])
        df_signals["confidence"] = model.predict_proba(X_scaled)[:, 1]
        st.dataframe(df_signals[["symbol", "timestamp", "confidence"] + feature_cols].head())

        st.subheader("🔬 SHAP Feature Importance")
        explainer = shap.Explainer(model, X_scaled)
        shap_values = explainer(X_scaled)
        fig, ax = plt.subplots()
        shap.plots.beeswarm(shap_values, show=False)
        st.pyplot(fig)

# --- Live Signal Queue ---
elif view == "Live Signal Queue":
    st.header("📡 Live Signal Queue")
    signal_log_path = "logs/live_signals.csv"

    if os.path.exists(signal_log_path):
        signal_df = pd.read_csv(signal_log_path)
        if not signal_df.empty:
            strategies = signal_df["strategy"].dropna().unique().tolist()
            selected_signal_strategy = st.selectbox("Filter signals by strategy:", ["All"] + sorted(strategies))

            if selected_signal_strategy != "All":
                signal_df = signal_df[signal_df["strategy"] == selected_signal_strategy]

            if "confidence" in signal_df.columns:
                conf_range = st.slider("Filter by confidence:", 0.0, 1.0, (0.0, 1.0))
                signal_df = signal_df[(signal_df["confidence"] >= conf_range[0]) & (signal_df["confidence"] <= conf_range[1])]

            st.dataframe(signal_df.head(100))
        else:
            st.info("No signals currently in queue.")
    else:
        st.warning("live_signals.csv not found. Queue not yet initialized.")

# --- Backtesting Results ---
elif view == "Backtesting Results":
    st.header("📈 Backtesting Results")
    trade_log_path = "logs/trades_log.csv"

    if os.path.exists(trade_log_path):
        trades_df = pd.read_csv(trade_log_path)
        if not trades_df.empty:
            all_strategies = [
                "orb_breakout", "vwap_slingshot", "trend_continuation",
                "gap_vwap_reclaim", "high_volume_gap", "late_day_reversal",
                "pullback_resumption", "rolling_reversal", "sector_rotation",
                "tod_trend_bias"
            ]
            strategies = sorted(set(all_strategies))

            for strat in sorted(strategies):
                with st.expander(f"📊 {strat.title()} Strategy Performance"):
                    tabs = st.tabs(["Days", "Weeks", "Months"])
                    timeframes = ["D", "W", "M"]

                    for i, tf in enumerate(timeframes):
                        with tabs[i]:
                            try:
                                trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"], errors="coerce")
                                df = trades_df[trades_df["strategy"] == strat].copy()
                                df.set_index("timestamp", inplace=True)
                                df_grouped = df.resample(tf).agg({
                                    "symbol": "count",
                                    "strategy": "first",
                                    "direction": "last",
                                    "entry": "last",
                                    "final": "last",
                                    "win_rate": "mean",
                                    "pnl": "sum",
                                    "confidence": "mean"
                                }).rename(columns={
                                    "symbol": "# Trades",
                                    "entry": "Entry",
                                    "final": "Final",
                                    "win_rate": "Win R",
                                    "pnl": "P&L",
                                    "confidence": "Confidence"
                                })
                                df_grouped.reset_index(inplace=True)
                                st.dataframe(df_grouped[["timestamp", "# Trades", "strategy", "direction", "Entry", "Final", "Win R", "P&L", "Confidence"]].head(30))
                            except Exception as e:
                                st.warning(f"Could not load {tf} data for {strat}: {e}")
        else:
            st.info("Trade log found but is empty.")
    else:
        st.warning("Trade log not found. Backtesting data unavailable.")


# --- Live Results ---
from polygon_stream import get_atr_snapshot
elif view == "Live":
    st.header("📡 Live Strategy Performance")

    st.subheader("⛔ ATR Skip Log Viewer")
    atr_skip_log = "logs/skipped_due_to_atr.csv"
    if os.path.exists(atr_skip_log):
        try:
            skip_df = pd.read_csv(atr_skip_log)
            skip_df["timestamp"] = pd.to_datetime(skip_df["timestamp"], errors="coerce")
            symbols = skip_df["symbol"].unique().tolist()
            selected_symbol = st.selectbox("Filter by symbol:", ["All"] + sorted(symbols))

            min_date = skip_df["timestamp"].min().date()
            max_date = skip_df["timestamp"].max().date()
            start_date, end_date = st.date_input("Select date range:", [min_date, max_date])

            if selected_symbol != "All":
                skip_df = skip_df[skip_df["symbol"] == selected_symbol]

            skip_df = skip_df[(skip_df["timestamp"].dt.date >= start_date) & (skip_df["timestamp"].dt.date <= end_date)]
            st.dataframe(skip_df.tail(100))

            st.subheader("📈 Skips by Symbol")
            skip_freq = skip_df["symbol"].value_counts()
            st.bar_chart(skip_freq)

            # Auto-flag frequently skipped symbols
            st.subheader("⚠️ Frequently Skipped Symbols")
            flagged = skip_freq[skip_freq >= 3]  # Customize threshold here
            if not flagged.empty:
                st.warning("These symbols have been skipped 3 or more times recently:")
                st.dataframe(flagged.reset_index().rename(columns={"index": "Symbol", "symbol": "Skip Count"}))
                muted_path = "config/muted_symbols.json"
                try:
                    import json
                    with open(muted_path, "w") as f:
                        json.dump({"muted": flagged.index.tolist()}, f)
                    st.success(f"Muted {len(flagged)} symbols for future filtering.")

                st.subheader("🔧 Selectively Unmute Symbols")
                unmute_selected = st.multiselect("Choose symbols to unmute:", flagged.index.tolist())
                if st.button("🔓 Unmute Selected"):
                    try:
                        import json
                        with open(muted_path, "r") as f:
                            current = json.load(f)
                        updated = [sym for sym in current.get("muted", []) if sym not in unmute_selected]
                        with open(muted_path, "w") as f:
                            json.dump({"muted": updated}, f)
                        st.success(f"Unmuted {len(unmute_selected)} symbols.")
                    except Exception as e:
                        st.error(f"Error updating muted list: {e}")

                if st.button("🔓 Unmute All Symbols"):
                    try:
                        import json
                        with open(muted_path, "w") as f:
                            json.dump({"muted": []}, f)
                        st.success("All symbols unmuted.")
                    except Exception as e:
                        st.error(f"Failed to clear muted symbols: {e}")
                except Exception as e:
                    st.error(f"Error writing muted list: {e}")
                st.dataframe(flagged.reset_index().rename(columns={"index": "Symbol", "symbol": "Skip Count"}))
            else:
                st.success("No symbols currently exceed skip threshold.")
        except Exception as e:
            st.warning(f"Could not load ATR skip log: {e}")
    else:
        st.info("ATR skip log not found.")

    st.subheader("📡 Live ATR Snapshot")
    atr_threshold = st.number_input("Set ATR trade threshold:", min_value=0.0, max_value=10.0, value=3.0, step=0.1)
    try:
        with open("config/atr_config.json", "w") as cfg:
            import json
            json.dump({"atr_threshold": atr_threshold}, cfg)
    except Exception as e:
        st.warning(f"Unable to save ATR threshold: {e}")
    st.write(f"Trades will be skipped when ATR exceeds {atr_threshold}")
    try:
        atr_data = get_atr_snapshot()
        atr_df = pd.DataFrame(list(atr_data.items()), columns=["Symbol", "ATR"])
        atr_df_filtered = atr_df[atr_df['ATR'] <= atr_threshold]
        st.dataframe(atr_df_filtered)
    except Exception as e:
        st.warning(f"Unable to load ATR snapshot: {e}")
    trade_log_path = "logs/live_trades_log.csv"

    if os.path.exists(trade_log_path):
        trades_df = pd.read_csv(trade_log_path)
        if not trades_df.empty:
            all_strategies = [
                "orb_breakout", "vwap_slingshot", "trend_continuation",
                "gap_vwap_reclaim", "high_volume_gap", "late_day_reversal",
                "pullback_resumption", "rolling_reversal", "sector_rotation",
                "tod_trend_bias"
            ]
            strategies = sorted(set(all_strategies))

            for strat in sorted(strategies):
                with st.expander(f"📊 {strat.title()} Strategy Live Data"):
                    df_strat = trades_df[trades_df["strategy"] == strat].copy()
                    if df_strat.empty:
                        st.info("No data available for this strategy yet.")
                        continue
                    tabs = st.tabs(["Days", "Weeks", "Months"])
                    timeframes = ["D", "W", "M"]

                    for i, tf in enumerate(timeframes):
                        with tabs[i]:
                            try:
                                trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"], errors="coerce")
                                df = trades_df[trades_df["strategy"] == strat].copy()
                                df.set_index("timestamp", inplace=True)
                                df_grouped = df.resample(tf).agg({
                                    "symbol": "count",
                                    "strategy": "first",
                                    "direction": "last",
                                    "entry": "last",
                                    "final": "last",
                                    "win_rate": "mean",
                                    "pnl": "sum",
                                    "confidence": "mean"
                                }).rename(columns={
                                    "symbol": "# Trades",
                                    "entry": "Entry",
                                    "final": "Final",
                                    "win_rate": "Win R",
                                    "pnl": "P&L",
                                    "confidence": "Confidence"
                                })
                                df_grouped.reset_index(inplace=True)
                                st.dataframe(df_grouped[["timestamp", "# Trades", "strategy", "direction", "Entry", "Final", "Win R", "P&L", "Confidence"]].head(30))
                            except Exception as e:
                                st.warning(f"Could not load {tf} data for {strat}: {e}")
        else:
            st.info("Live trade log found but is empty.")
    else:
        st.warning("Live trade log not found. Live trading data unavailable.")


# --- Model Trainer ---
elif view == "Model Trainer":
    st.header("🧪 Model Trainer: Strategy Parameter Tester")

    import itertools

    strategies = {
        "orb_breakout": {
            "threshold": [0.3, 0.5, 0.7],
            "risk_multiplier": [0.5, 0.75, 1.0]
        },
        "trend_continuation": {
            "window_size": [10, 20],
            "threshold": [0.4, 0.6]
        }
        # Add more strategies and parameters as needed
    }

    selected_strategy = st.selectbox("Select strategy to test:", list(strategies.keys()))
    param_grid = strategies[selected_strategy]

    grids = list(itertools.product(*param_grid.values()))
    st.caption(f"Generated {len(grids)} parameter combinations")

    test_configs = []
    for g in grids:
        config = dict(zip(param_grid.keys(), g))
        test_configs.append(config)

    if st.button("Run Parameter Test Batch"):
        st.info("Running test passes (mocked)...")
        results = []
        for cfg in test_configs:
            win_rate = round(0.5 + 0.05 * (cfg.get("threshold", 0.5)), 2)
            pnl = round(1000 * cfg.get("risk_multiplier", 1), 2)
            results.append({**cfg, "Win Rate": win_rate, "P&L": pnl})
        results_df = pd.DataFrame(results)
        st.dataframe(results_df)

        st.subheader("📊 High-Performance Configs")
        best = results_df[(results_df["Win Rate"] >= 0.55) & (results_df["P&L"] > 750)]
        st.dataframe(best)

        if not best.empty and st.button("Promote Best Config"):
            st.success("Best config approved for deployment!")

# --- Resume Strategies ---
elif view == "Resume Strategies":
    st.header("▶️ Resume Paused Strategies")
    resume_file = "logs/resume_requests.json"
    all_strategies = [
        "orb_breakout", "vwap_slingshot", "trend_continuation",
        "gap_vwap_reclaim", "high_volume_gap", "late_day_reversal",
        "pullback_resumption", "rolling_reversal", "sector_rotation",
        "tod_trend_bias"
    ]

    selected_paused = st.selectbox("Select a strategy to resume:", all_strategies)
    if st.button("📤 Submit Resume Request"):
        try:
            os.makedirs("logs", exist_ok=True)
            with open(resume_file, "w") as f:
                f.write(f'{{"resume": "{selected_paused}"}}')
            st.success(f"Resume request for {selected_paused} saved to resume_requests.json")
        except Exception as e:
            st.error(f"Error writing resume request: {e}")

# --- Strategy Error Viewer ---
elif view == "Strategy Errors":
    st.header("🛠 Strategy Error Log Viewer")
    error_log_path = "logs/strategy_errors.csv"

    if os.path.exists(error_log_path):
        error_df = pd.read_csv(error_log_path)
        if not error_df.empty:
            strategies = error_df['strategy'].dropna().unique().tolist()
            selected_strategy = st.selectbox("Filter by strategy:", ["All"] + sorted(strategies))

            error_df["timestamp"] = pd.to_datetime(error_df["timestamp"], errors="coerce")
            min_date = error_df["timestamp"].min().date()
            max_date = error_df["timestamp"].max().date()
            start_date, end_date = st.date_input("Select date range:", [min_date, max_date])

            if selected_strategy != "All":
                error_df = error_df[error_df["strategy"] == selected_strategy]
            error_df = error_df[(error_df["timestamp"].dt.date >= start_date) & (error_df["timestamp"].dt.date <= end_date)]

            st.dataframe(error_df)

            # 📊 Error Frequency Chart
            st.subheader("📈 Error Frequency by Strategy")
            freq_chart = error_df.groupby("strategy")["timestamp"].count().sort_values(ascending=False)
            st.bar_chart(freq_chart)

            # 📥 Download filtered log
            st.download_button(
                label="Download Filtered Log as CSV",
                data=error_df.to_csv(index=False),
                file_name="filtered_strategy_errors.csv",
                mime="text/csv"
            )

            with st.expander("🧹 Cleanup Options"):
                if st.button("Clear Error Log"):
                    open(error_log_path, "w").close()
                    st.success("Strategy error log has been cleared.")
        else:
            st.info("No errors currently logged.")
    else:
        st.warning("strategy_errors.csv not found. No strategy errors have been logged yet.")

        if st.button("💥 Generate Test Error"):
            os.makedirs("logs", exist_ok=True)
            with open(error_log_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "strategy", "symbol", "error_message"])
                writer.writeheader()
                writer.writerow({
                    "timestamp": datetime.utcnow().isoformat(),
                    "strategy": "trend_continuation",
                    "symbol": "AAPL",
                    "error_message": "KeyError: 'volume'"
                })
            st.success("Test error log generated.")

