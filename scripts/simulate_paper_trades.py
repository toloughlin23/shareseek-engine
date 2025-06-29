from engine.promotion_manager import update_symbol, evaluate_promotion

symbol = "TSLA"

# Simulate trade results
results = ["win"] * 6 + ["loss"] * 4  # 10 trades, 60% win rate

for result in results:
    update_symbol(symbol, result)

# Evaluate for promotion
if evaluate_promotion(symbol):
    print(f"{symbol} has been promoted to live.")
else:
    print(f"{symbol} remains in paper mode.")
