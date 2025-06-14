#!/usr/bin/env python3
import os, json, argparse
from datetime import datetime, timezone
import pandas as pd
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import APIError
import requests, yfinance as yf

def init_api():
    key    = os.getenv("APCA_API_KEY_ID")
    secret = os.getenv("APCA_API_SECRET_KEY")
    base   = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
    return tradeapi.REST(key, secret, base)

def load_config(path="../config.json"):
    with open(path) as f:
        return json.load(f)

def fetch_daily_bars(api, symbol, start, end):
    s = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    e = end.  strftime("%Y-%m-%dT%H:%M:%SZ")
    for feed in ("sip", "iex"):
        try:
            df = api.get_bars(symbol, tradeapi.TimeFrame.Day,
                              start=s, end=e, limit=1000, feed=feed).df
            df = df.tz_convert(None).reset_index().set_index("timestamp")
            print(f"  → Fetched {symbol} via {feed.upper()}")
            return df
        except (APIError, requests.exceptions.HTTPError) as err:
            if "403" in str(err).lower() or "forbidden" in str(err).lower():
                print(f"  ⚠️  {feed.upper()} forbidden, trying next…")
                continue
            raise
    print(f"  🔄 Falling back to yfinance for {symbol}")
    df_yf = yf.download(symbol,
                       start=start.strftime("%Y-%m-%d"),
                       end=(end + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                       progress=False, auto_adjust=False)
    if df_yf.empty:
        raise RuntimeError(f"No yfinance data for {symbol}")
    df_yf.index = pd.to_datetime(df_yf.index)
    df_yf.index.name = "timestamp"
    df = df_yf.rename(columns={
        "Open":"open","High":"high","Low":"low",
        "Close":"close","Volume":"volume"
    })
    print(f"  ✅ Fetched {symbol} via yfinance")
    return df

def run_ema_crossover_backtest(df, short=9, long=21):
    data = df[["close"]].copy()
    data["ema_s"] = data["close"].ewm(span=short, adjust=False).mean()
    data["ema_l"] = data["close"].ewm(span=long,  adjust=False).mean()
    data["signal"]   = (data["ema_s"] > data["ema_l"]).astype(int)
    data["position"] = data["signal"].diff().fillna(0)

    # Use Python lists instead of .tolist()
    closes    = list(data["close"])
    positions = list(data["position"])

    trades = []
    in_long = False
    entry   = None

    for pos, price in zip(positions, closes):
        if pos == 1 and not in_long:
            in_long = True
            entry   = price
        elif pos == -1 and in_long:
            trades.append((entry, price))
            in_long = False

    if in_long:
        trades.append((entry, closes[-1]))

    returns = [(exit - entry)/entry for entry, exit in trades]
    n        = len(returns)
    total    = sum(returns)
    win_rate = sum(r>0 for r in returns)/n if n else 0
    avg_ret  = sum(returns)/n if n else 0
    pf       = (
        sum(r for r in returns if r>0) /
        -sum(r for r in returns if r<0)
        if any(r<0 for r in returns) else float("inf")
    )

    return {
        "num_trades":    n,
        "total_return":  total,
        "win_rate":      win_rate,
        "avg_return":    avg_ret,
        "profit_factor": pf,
    }

def main():
    p = argparse.ArgumentParser("Backtest EMA Crossover")
    p.add_argument("--strategy", default="EMA Crossover")
    p.add_argument("--start",    required=True)
    p.add_argument("--end",      required=True)
    p.add_argument("--short",    type=int, default=9)
    p.add_argument("--long",     type=int, default=21)
    args = p.parse_args()

    api  = init_api()
    cfg  = load_config()
    syms = cfg["strategies"].get(args.strategy, {}).get("symbols", [])
    if not syms:
        print(f"No symbols in config for '{args.strategy}'"); return

    start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    end   = datetime.fromisoformat(args.end).  replace(tzinfo=timezone.utc)

    print(f"\nBacktesting '{args.strategy}' {args.start}→{args.end}")
    print(f" EMA spans: short={args.short}, long={args.long}\n")

    for sym in syms:
        print(f"-- {sym} --")
        try:
            df = fetch_daily_bars(api, sym, start, end)
        except Exception as e:
            print(f"  ❌ Fetch error: {e}\n"); continue

        if len(df) < args.long*2:
            print("  ⚠️  Not enough data\n"); continue

        stats = run_ema_crossover_backtest(df, short=args.short, long=args.long)
        print(f"  Trades:        {stats['num_trades']}")
        print(f"  Total Return:  {stats['total_return']*100:.2f}%")
        print(f"  Win Rate:      {stats['win_rate']*100:.2f}%")
        print(f"  Avg Return:    {stats['avg_return']*100:.2f}%")
        print(f"  Profit Factor: {stats['profit_factor']:.2f}\n")

if __name__ == "__main__":
    main()
