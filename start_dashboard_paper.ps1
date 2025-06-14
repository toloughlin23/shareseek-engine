cd C:\Users\tolou\trading_dashboard

$env:APCA_API_KEY_ID = "PKG7KD1YOVP9GXEHSWB9"
$env:APCA_API_SECRET_KEY = "9t0shXeGWlApnkHVqzepkuyf6XFBHymWhaz2OTRi"
$env:APCA_API_BASE_URL = "https://paper-api.alpaca.markets"

streamlit run dashboard.py
