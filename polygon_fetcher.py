import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# Load your Polygon API key
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY") or "pMtj26Qxlt1SJhv8uOEAJ2rXwpE9EzzG"

# Output folders
FETCH_PATH = "data/backtest_data"
MERGED_PATH = "data/backtest_merged"
os.makedirs(FETCH_PATH, exist_ok=True)
os.makedirs(MERGED_PATH, exist_ok=True)

def get_last_weekday():
    today = datetime.now()
    for i in range(1, 7):
        candidate = today - timedelta(days=i)
        if candidate.weekday() < 5:  # Monday=0, Sunday=6
            return candidate.strftime("%Y-%m-%d")

def fetch_polygon_data(symbol, date):
    print(f"🔄 Fetching data for {symbol} on {date}...")

    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/minute/"
        f"{date}/{date}?adjusted=true&sort=asc&limit=50000&apiKey={POLYGON_API_KEY}"
    )

    r = requests.get(url)
    if r.status_code != 200:
        print(f"❌ Error: {r.status_code} – {r.text}")
        return

    data = r.json().get("results", [])
    if not data:
        print(f"⚠️ No data returned for {symbol}")
        return

    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["t"], unit="ms")
    df.rename(columns={
        "o": "open",
        "h": "high",
        "l": "low",
        "c": "close",
        "v": "volume"
    }, inplace=True)

    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    fetch_file = os.path.join(FETCH_PATH, f"{symbol}_{date}.csv")
    df.to_csv(fetch_file, index=False)
    print(f"✅ Saved: {fetch_file}")

def merge_symbol_data(symbol):
    print(f"🔗 Merging historical data for {symbol}...")
    all_files = [f for f in os.listdir(FETCH_PATH) if f.startswith(symbol) and f.endswith(".csv")]
    if not all_files:
        print(f"⚠️ No files found for {symbol} in backtest_data/")
        return

    all_dfs = [pd.read_csv(os.path.join(FETCH_PATH, f)) for f in sorted(all_files)]
    combined_df = pd.concat(all_dfs).drop_duplicates("timestamp").sort_values("timestamp")
    merged_file = os.path.join(MERGED_PATH, f"{symbol}.csv")
    combined_df.to_csv(merged_file, index=False)
    print(f"✅ Merged file saved: {merged_file}")

if __name__ == "__main__":
    symbols = ["AAPL", "MSFT"]
    date = get_last_weekday()

    for sym in symbols:
        fetch_polygon_data(sym, date)
        merge_symbol_data(sym)
