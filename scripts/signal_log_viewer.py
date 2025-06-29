# /scripts/signal_log_viewer.py (clean rewrite)

import pandas as pd
import time
from datetime import datetime

LOG_PATH = "logs/signals.csv"
REFRESH_INTERVAL = 10  # seconds


def display_latest_signals():
    print("\n📊 Live Signal Log Viewer\n-------------------------")
    seen_rows = 0

    while True:
        try:
            df = pd.read_csv(LOG_PATH, on_bad_lines='skip')

            print("\n📈 Summary Stats")
            print("----------------")
            total = len(df)
            accepted = (df['status'] == 'accepted').sum()
            rejected = total - accepted
            print(f"Total Signals: {total}")
            print(f"Accepted: {accepted} ({(accepted/total)*100:.1f}%)")
            print(f"Rejected: {rejected} ({(rejected/total)*100:.1f}%)")
            print("Top Rejection Reasons:")
            print(df[df['status'] == 'rejected']['reason'].value_counts().to_string())

            new_rows = df.iloc[seen_rows:]
            if not new_rows.empty:
                print("\n--- New Signals ---")

            for _, row in new_rows.iterrows():
                ts = datetime.fromisoformat(row['timestamp']).strftime('%H:%M:%S')
                print(f"[{ts}] {row['symbol']} | {row['status']} | Reason: {row.get('reason', '-')}")
                print(f"     Final: {row.get('final_score', '-')}, Context: {row.get('context_score', '-')}, Risk: {row.get('risk_pct', '-')}")

            seen_rows = len(df)

        except FileNotFoundError:
            print("Waiting for signals.csv to be created...")
        except Exception as e:
            print(f"Error reading log: {e}")

        time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    display_latest_signals()
