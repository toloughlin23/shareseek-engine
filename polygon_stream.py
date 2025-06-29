import websocket
import json
import threading
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ✅ CONFIG
API_KEY = "YOUR_POLYGON_API_KEY"
SYMBOLS = ["AAPL", "MSFT", "GOOG"]  # Replace with your active symbol list

# ✅ IN-MEMORY STORAGE
from collections import deque
from statistics import mean

live_prices = {}
price_history = {}
news_feed = []

# ✅ INIT SENTIMENT ANALYZER
analyzer = SentimentIntensityAnalyzer()

# ✅ HANDLE INCOMING MESSAGES
def on_message(ws, message):
    data = json.loads(message)
    for event in data:
        ev_type = event.get("ev")

        if ev_type == "AM":  # Minute bar update
            symbol = event["sym"]
            price = event["c"]
            live_prices[symbol] = price

            # Track history and compute ATR
            if symbol not in price_history:
                price_history[symbol] = deque(maxlen=15)
            price_history[symbol].append(price)

            if len(price_history[symbol]) >= 14:
                diffs = [abs(price_history[symbol][i] - price_history[symbol][i - 1]) for i in range(1, len(price_history[symbol]))]
                live_prices[f"{symbol}_atr"] = round(mean(diffs), 4)
            print(f"[PRICE] {symbol}: ${price}")

        elif ev_type == "n":  # News update
            symbol = event["sym"]
            headline = event["headline"]
            timestamp = event.get("timestamp")
            sentiment = analyzer.polarity_scores(headline)["compound"]
            news_item = {
                "symbol": symbol,
                "headline": headline,
                "score": sentiment,
                "timestamp": timestamp
            }
            news_feed.append(news_item)
            print(f"[NEWS] {symbol}: {headline} | Sentiment: {sentiment}")

# ✅ ON CONNECT
def on_open(ws):
    ws.send(json.dumps({"action": "auth", "params": API_KEY}))
    for symbol in SYMBOLS:
        ws.send(json.dumps({"action": "subscribe", "params": f"AM.{symbol}"}))
    ws.send(json.dumps({"action": "subscribe", "params": "n.*"}))  # Subscribe to all news
    print("✅ Subscribed to real-time price & news streams")

# ✅ ERROR AND CLOSE HANDLING
def on_error(ws, error): print(f"[ERROR] {error}")
def on_close(ws, code, msg): print("🔌 WebSocket closed")

# ✅ START STREAM
def run_polygon_stream():
    url = "wss://socket.polygon.io/stocks"
    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

# ✅ LAUNCH IN BACKGROUND THREAD
if __name__ == "__main__":
    t = threading.Thread(target=run_polygon_stream)
    t.start()
