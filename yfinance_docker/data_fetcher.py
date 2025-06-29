import yfinance as yf
import pandas as pd
import json
import os

symbols = ["AAPL", "MSFT", "TSLA", "GOOGL", "NVDA"]
DATA_DIR = "/app/data"

print("📥 Fetching stock data for multiple symbols...\n")

for symbol in symbols:
    print(f"🔄 {symbol}...")
    
    try:
        # Download historical OHLCV data
        df = yf.download(symbol, start="2023-01-01", end="2023-12-31")
        df.to_csv(os.path.join(DATA_DIR, f"{symbol}_data.csv"))
        print(f"✅ OHLCV saved: {symbol}_data.csv")

        # Download basic fundamentals
        ticker = yf.Ticker(symbol)
        info = ticker.info

        fundamentals = {
            "symbol": symbol,
            "trailingPE": info.get("trailingPE"),
            "forwardEps": info.get("forwardEps"),
            "debtToEquity": info.get("debtToEquity"),
            "marketCap": info.get("marketCap"),
            "dividendYield": info.get("dividendYield"),
            "sector": info.get("sector"),
            "industry": info.get("industry")
        }

        with open(os.path.join(DATA_DIR, f"{symbol}_fundamentals.json"), "w") as f:
            json.dump(fundamentals, f, indent=2)

        print(f"📊 Fundamentals saved: {symbol}_fundamentals.json\n")

    except Exception as e:
        print(f"❌ Error with {symbol}: {e}\n")
