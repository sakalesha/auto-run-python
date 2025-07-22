import pyotp
import pandas as pd
from SmartApi import SmartConnect
from datetime import datetime, timedelta
import time
import requests

# ----------------- CONFIGURATION -----------------

API_KEY = "ogR4lGea"
CLIENT_ID = "AAAQ351436"
PASSWORD = "2004"
TOTP_SECRET = "HDVDEP5OZI4JZEUSJJYI2O472M"

SECTOR_CSV = "sectors.csv"
EXCHANGE = "NSE"

# Telegram Config
TELEGRAM_BOT_TOKEN = "7959899285:AAHxaB75sAZfu_wW7PnoUEcbA-WqLQSlmdM"
TELEGRAM_CHAT_ID = "6640875299"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("❌ Telegram Error:", e)

# ----------------- LOGIN -----------------

totp = pyotp.TOTP(TOTP_SECRET).now()
obj = SmartConnect(api_key=API_KEY)

try:
    data = obj.generateSession(CLIENT_ID, PASSWORD, totp)
    refreshToken = data['data']['refreshToken']
    res = obj.getProfile(refreshToken)
    print("✅ Login Successful")
except Exception as e:
    print("❌ Login failed:", e)
    exit()

# ----------------- LOAD SECTOR TOKENS -----------------

sectors_df = pd.read_csv(SECTOR_CSV)
results = []

# ----------------- DATE RANGE FOR HISTORICAL -----------------

today = datetime.now()
yesterday = today - timedelta(days=1)
from_date = yesterday.replace(hour=15, minute=29)
to_date = yesterday.replace(hour=15, minute=30)

from_str = from_date.strftime('%Y-%m-%d %H:%M')
to_str = to_date.strftime('%Y-%m-%d %H:%M')

# ----------------- PROCESS EACH SECTOR -----------------

for idx, row in sectors_df.iterrows():
    symbol = row['symbol']
    token = str(row['token'])

    try:
        # Get previous day's close price
        historicParams = {
            "exchange": EXCHANGE,
            "symboltoken": token,
            "interval": "ONE_MINUTE",
            "fromdate": from_str,
            "todate": to_str
        }
        hist_data = obj.getCandleData(historicParams)
        prev_close = hist_data['data'][-1][4]  # Close of last candle

        # Get LTP (live price)
        ltp_data = obj.ltpData(EXCHANGE, symbol, token)
        ltp = float(ltp_data['data']['ltp'])

        # Calculate % change
        pct_change = ((ltp - prev_close) / prev_close) * 100
        results.append((symbol, prev_close, ltp, round(pct_change, 2)))

    except Exception as e:
        print(f"⚠️ Error for {symbol}: {e}")
        continue

# ----------------- DISPLAY RESULTS -----------------

results_df = pd.DataFrame(results, columns=["Sector", "Prev Close", "LTP", "% Change"])
results_df = results_df.sort_values(by="% Change", ascending=False)

print("\n📊 Sector Performance (% Change):\n")
print(results_df.to_string(index=False))

top_gainer = results_df.iloc[0]
top_loser = results_df.iloc[-1]

print(f"\n🚀 Top Gainer: {top_gainer['Sector']} ({top_gainer['% Change']}%)")
print(f"📉 Top Loser: {top_loser['Sector']} ({top_loser['% Change']}%)")

# ----------------- Read Sentiment from File -----------------
try:
    with open("sentiment.txt", "r") as f:
        sentiment = f.read().strip()
except FileNotFoundError:
    print("❌ Sentiment file not found. Run market_sentiment.py first.")
    exit()

# ----------------- Decide Focus Sector -----------------
if sentiment == "Bullish":
    focus_sector = top_gainer
elif sentiment == "Bearish":
    focus_sector = top_loser
else:
    focus_sector = None

print(f"\n📌 Market Sentiment: {sentiment}")
if focus_sector is not None:
    print(f"🎯 Focus Sector Based on Sentiment: {focus_sector['Sector']} ({focus_sector['% Change']}%)")
else:
    print("ℹ️ No specific focus sector (Neutral sentiment).")

# ----------------- SEND TELEGRAM ALERT (FOCUS SECTOR ONLY) -----------------

if focus_sector is not None:
    msg = f"🎯 *Focus Sector Based on Sentiment:*\n{focus_sector['Sector']} ({focus_sector['% Change']}%)"
    send_telegram(msg)
else:
    msg = "ℹ️ *No specific focus sector (Neutral sentiment).*"
    send_telegram(msg)
