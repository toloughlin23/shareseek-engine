from flask import Flask, request, jsonify
import json, os, time, pandas as pd, datetime, csv
import alpaca_trade_api as tradeapi

# === CONFIG ===
CONFIG_FILE = "config.json"
STATE_FILE = "trading_state.json"
TRADE_LOG = "logs/trades_log.csv"
WEBHOOK_API_KEY = "PK50M2HOM0PZ0NDKV93M"
PAPER_BASE_URL = "https://paper-api.alpaca.markets"
COOLDOWN_SECONDS = 300  # 5 minutes

# === Load Config ===
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

MAX_DAILY_LOSS = config["global_settings"].get("max_drawdown", 500)

# === Load/Init State ===
if not os.path.exists(STATE_FILE):
    state = {"global": {"daily_loss": 0}, "last_trades": {}}
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
else:
    with open(STATE_FILE, "r") as f:
        state = json.load(f)

# === Connect to Alpaca ===
ALPACA_API_KEY = os.getenv("APCA_API_KEY_ID")
ALPACA_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, PAPER_BASE_URL)

# === Flask App ===
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True)
    print("📩 Received:", data)

    if not data or data.get("key") != WEBHOOK_API_KEY:
        return jsonify({"error": "Invalid or missing API key"}), 403

    strategy = data.get("strategy")
    symbol = data.get("symbol")
    action = data.get("action")

    if not all([strategy, symbol, action]):
        return jsonify({"error": "Missing required fields"}), 400

    strat_cfg = config["strategies"].get(strategy)
    if not strat_cfg or not strat_cfg.get("enabled") or strat_cfg.get("paused"):
        return jsonify({"message": f"Strategy '{strategy}' is inactive or paused."}), 200

    if symbol not in strat_cfg["symbols"]:
        return jsonify({"message": f"Symbol {symbol} not allowed for strategy {strategy}."}), 200

    # === Cooldown Check ===
    now = time.time()
    last_trade = state.get("last_trades", {}).get(symbol)
    if last_trade and now - last_trade < COOLDOWN_SECONDS:
        return jsonify({"message": f"⏱ Cooldown active for {symbol}"}), 200

    # === Circuit Breaker Check ===
    if os.path.exists(TRADE_LOG):
        try:
            df = pd.read_csv(TRADE_LOG)
            today = pd.Timestamp.now().normalize()
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            daily_pnl = df[df["timestamp"] >= today]["pnl"].fillna(0).sum()
            if daily_pnl <= -MAX_DAILY_LOSS:
                return jsonify({"message": "🚨 Circuit breaker: Max daily loss hit"}), 200
        except Exception as e:
            print(f"⚠️ Could not read trade log: {e}")

    # === Submit Order ===
    try:
        account = api.get_account()
        allocation = strat_cfg["allocation"] / 100
        order_value = max(1.00, round(float(account.cash) * allocation, 2))  # ensure $1 minimum

        api.submit_order(
            symbol=symbol,
            qty=None,
            notional=order_value,
            side=action.lower(),
            type="market",
            time_in_force="day"  # Required for fractional notional orders
        )

        print(f"✅ {action.upper()} {symbol} with ${order_value} for {strategy}")
        state.setdefault("last_trades", {})[symbol] = now

        # === Log trade ===
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "strategy": strategy,
            "symbol": symbol,
            "side": action.lower(),
            "notional": order_value,
            "pnl": ""  # Placeholder for future fill data
        }

        file_exists = os.path.exists(TRADE_LOG)
        with open(TRADE_LOG, "a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=log_entry.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(log_entry)

        # Save updated state
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)

        return jsonify({"message": "✅ Order placed"}), 200

    except Exception as e:
        print(f"❌ Order error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5001)
