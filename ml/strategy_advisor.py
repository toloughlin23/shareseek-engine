# /ml/strategy_advisor.py

import os
import pandas as pd
from datetime import datetime, timedelta

TRADE_OUTCOME_LOG = "logs/trade_outcomes.csv"
DEFAULT_LOOKBACK_DAYS = 30


def load_trade_data(path=TRADE_OUTCOME_LOG, days=DEFAULT_LOOKBACK_DAYS):
    if not os.path.exists(path):
        print("🚫 No trade outcome data found.")
        return pd.DataFrame()

    df = pd.read_csv(path, parse_dates=["entry_time", "exit_time"])
    cutoff = datetime.now() - timedelta(days=days)
    return df[df["exit_time"] >= cutoff]


def compute_strategy_scores(df):
    if df.empty:
        return {}
    grouped = df.groupby("strategy")["reward"]
    return grouped.mean().sort_values(ascending=False).round(4).to_dict()


def recommend_weights(strategy_scores, base_weight=1.0):
    if not strategy_scores:
        return {}

    max_reward = max(strategy_scores.values()) or 1.0
    return {
        strat: round((score / max_reward) * base_weight, 3)
        for strat, score in strategy_scores.items()
    }


def score_and_recommend(days=DEFAULT_LOOKBACK_DAYS):
    df = load_trade_data(days=days)
    scores = compute_strategy_scores(df)
    weights = recommend_weights(scores)
    print("\n📊 Strategy Performance (avg reward):")
    print(scores)
    print("\n📈 Recommended Weights:")
    print(weights)
    return weights


if __name__ == "__main__":
    score_and_recommend()
