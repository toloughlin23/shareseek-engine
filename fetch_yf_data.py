import yfinance as yf
import os

# List of symbols to download
symbols = ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN"]

# Date range
start_date = "2023-01-01"
end_date = "2023-12-31"

# Output folder
data_path = "data/backtest_data"
os.makedirs(data_path, exist_ok=True)

for symbol in symbols:
    print(f"Downloading {symbol}...")
    df = yf.download(symbol, start=start_date, end=end_date, interval="1m")
    if df.empty:
        print(f"⚠️ No data found for {symbol}")
        continue

    df.reset_index(inplace=True)
    df.rename(columns={
        "Datetime": "time",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    }, inplace=True)

    file_path = os.path.join(data_path, f"{symbol}.csv")
    df.to_csv(file_path, index=False)
    print(f"✅ Saved to {file_path}")
