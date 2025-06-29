import os
import pandas as pd
import alpaca_trade_api as tradeapi
import logging

logging.basicConfig(level=logging.INFO)

# API creds from env
API_KEY = os.getenv("APCA_API_KEY_ID")
SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"

api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL)

# Load price data
symbol = "AAPL"
data_path = f"/app/data/{symbol}_data.csv"
df = pd.read_csv(data_path)

# Calculate ATR14
df["high_low"] = df["High"] - df["Low"]
df["ATR14"] = df["high_low"].rolling(window=14).mean()

atr = df["ATR14"].iloc[-1]
if pd.isna(atr) or atr == 0:
    logging.warning(f"{symbol}: ATR is invalid, skipping.")
    exit()

# Risk settings
account = api.get_account()
account_value = float(account.equity)
risk_pct = 0.01  # 1% risk per trade
max_risk = account_value * risk_pct
stop_distance = atr  # 1× ATR stop

# Calculate position size
qty = int(max_risk / stop_distance)
latest_price = df["Close"].iloc[-1]
position_value = qty * latest_price

logging.info(f"{symbol}: ATR=${atr:.2f}, Qty={qty}, Risk=${max_risk:.2f}, Position=${position_value:.2f}")

# Submit trade
api.submit_order(
    symbol=symbol,
    qty=qty,
    side="buy",
    type="market",
    time_in_force="day"
)

logging.info(f"{symbol}: ✅ Order submitted for {qty} shares at ${latest_price:.2f}")
