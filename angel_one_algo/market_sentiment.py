from SmartApi.smartConnect import SmartConnect
import pandas as pd
import time
from datetime import datetime
import pyotp

# ------------------- Credentials -------------------
API_KEY = "YPHELlmR"
CLIENT_ID = "AAAQ351436"
PIN = "2004"
TOTP_SECRET = "HDVDEP5OZI4JZEUSJJYI2O472M"

# ------------------- Nifty 50 Stocks -------------------
nifty50_symbols = {
    "ETERNAL", "GRASIM", "WIPRO", "JIOFIN", "BEL", "ASIANPAINT", "APOLLOHOSP", "JSWSTEEL",
    "BAJAJ-AUTO", "TATASTEEL", "INFY", "HEROMOTOCO", "EICHERMOT", "HDFCBANK", "SBIN", "SHRIRAMFIN",
    "ITC", "AXISBANK", "HCLTECH", "TCS", "LT", "TATAMOTORS", "HINDUNILVR", "POWERGRID", "M&M",
    "TRENT", "ONGC", "NESTLEIND", "RELIANCE", "KOTAKBANK", "BAJAJFINSV", "NTPC", "BAJFINANCE",
    "HDFCLIFE", "TATACONSUM", "CIPLA", "HINDALCO", "COALINDIA", "ICICIBANK", "BHARTIARTL",
    "ADANIPORTS", "ULTRACEMCO", "TITAN", "ADANIENT", "MARUTI", "SUNPHARMA", "SBILIFE", "TECHM",
    "DRREDDY", "INDUSINDBK"
}

# ------------------- Authenticate -------------------
totp = pyotp.TOTP(TOTP_SECRET).now()
obj = SmartConnect(api_key=API_KEY)
data = obj.generateSession(CLIENT_ID, PIN, totp)
authToken = data['data']['jwtToken']

# ------------------- Read All Equity Tokens -------------------
df = pd.read_csv("nse_equity_tokens.csv")

# Filter Nifty50 Tokens
nifty_df = df[df['name'].isin(nifty50_symbols)].copy()
nifty_tokens = nifty_df[['symbol', 'token']].values.tolist()

# ------------------- Get LTP and Compare -------------------
advances = 0
declines = 0
unchanged = 0

for symbol, token in nifty_tokens:
    try:
        ltp_data = obj.ltpData('NSE', symbol, token)
        current_price = ltp_data['data']['ltp']
        prev_close = ltp_data['data']['close']

        if current_price > prev_close:
            advances += 1
        elif current_price < prev_close:
            declines += 1
        else:
            unchanged += 1
    except Exception as e:
        print(f"Error fetching LTP for {symbol}: {e}")

# ------------------- Display Market Breadth -------------------
print(f"\nNifty 50 Market Breadth")
print(f"Advances : {advances}")
print(f"Declines : {declines}")
print(f"Unchanged: {unchanged}")

# ------------------- Determine Market Sentiment -------------------
if advances > declines:
    sentiment = "Bullish"
    direction = "Buy (Long)"
elif declines > advances:
    sentiment = "Bearish"
    direction = "Sell (Short)"
else:
    sentiment = "Neutral"
    direction = "No Trade"

print(f"\nMarket Sentiment: {sentiment}")
print(f"Suggested Trade Direction: {direction}")

# Save sentiment to file for sector.py to use
with open("sentiment.txt", "w") as f:
    f.write(sentiment)

