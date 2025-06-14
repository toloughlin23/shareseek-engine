import csv
from datetime import datetime
from flask import Flask, request, jsonify
import json
import os
import alpaca_trade_api as tradeapi

CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

ALPACA_API_KEY = os.getenv("APCA_API_KEY_ID")
ALPACA_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"
api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, BASE_URL)

app = Flask(__name__)
WEBHOOK_API_KEY = "PKG7KD1YOVP9GXEHSWB9"  # Replace if needed

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if data.get("key") != WEBHOOK_API_KEY:
        return jsonify({"error": "Invalid API key"}), 403

    strategy = data.get("strategy")
    symbol = data.get("symbol")
    action = data.get("action")

    allocation_pct = config["strategies"][strategy]["allocation"] / 100
    account = api.get_account()
    buying_power = float(account.cash)
    order_value = round(buying_power * allocation_pct, 2)

    side = action.lower()

    try:
        order = api.submit_order(
            symbol=symbol,
            notional=order_value,
            side=side,
            type="market",
            time_in_force="day"
        )

        # Log trade
        with open("./logs/trades_log.csv", "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                symbol,
                strategy,
                side,
                order_value,
                order.id
            ])

        return jsonify({"message": "Order placed"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5001)
