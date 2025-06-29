import os
import pandas as pd
from glob import glob

# 📁 Folder where daily CSVs are saved
data_folder = "data/backtest_data"
output_folder = "data/backtest_merged"
os.makedirs(output_folder, exist_ok=True)

# 🔍 Collect all files per symbol
symbol_files = {}
for filepath in glob(f"{data_folder}/*.csv"):
    filename = os.path.basename(filepath)
    if ".CSV.csv" in filename.upper():
        continue  # Skip incorrectly saved duplicate files
    symbol = filename.split("_")[0].split(".")[0].upper()
    symbol_files.setdefault(symbol, []).append(filepath)

# ⭮️ Merge and save per symbol
for symbol, files in symbol_files.items():
    df_list = []
    for f in files:
        try:
            df = pd.read_csv(f)
            df.columns = [c.strip().lower() for c in df.columns]  # sanitize column names

            # 🔄 Fix column naming if needed
            if "time" in df.columns and "timestamp" not in df.columns:
                df.rename(columns={"time": "timestamp"}, inplace=True)

            # Ensure timestamp column exists and is datetime
            if "timestamp" not in df.columns:
                df.insert(0, "timestamp", pd.date_range(start="2024-01-01", periods=len(df), freq="1min"))
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_localize(None)

            # Convert expected columns to numeric safely
            for col in ["open", "high", "low", "close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.dropna(subset=["open", "high", "low", "close", "volume"])  # drop rows with bad values

            df_list.append(df)
        except Exception as e:
            print(f"⚠️ Error reading {f}: {e}")

    if df_list:
        df_all = pd.concat(df_list, ignore_index=True)
        df_all = df_all.sort_values("timestamp")
        output_path = os.path.join(output_folder, f"{symbol}.csv")
        df_all.to_csv(output_path, index=False)
        print(f"✅ Merged: {symbol} → {output_path}")
    else:
        print(f"⚠️ No data found for {symbol}")
