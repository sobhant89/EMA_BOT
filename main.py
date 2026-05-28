import requests
import threading
import time
from telegram import Bot
from flask import Flask

# -----------------------
# TELEGRAM  (همان توکن و چت‌آیدی که دادی)
# -----------------------
BOT_TOKEN = "8546173398:AAEDnGYPuKKhWATYnZ8cbzFe3Q7kJ2AnkUQ"
CHAT_ID = "161280400"
bot = Bot(token=BOT_TOKEN)

# -----------------------
# FLASK KEEP ALIVE
# -----------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot running..."

# -----------------------
# EMA50
# -----------------------
def ema50(prices):
    k = 2 / 51
    ema = prices[0]
    for price in prices[1:]:
        ema = price * k + ema * (1 - k)
    return ema

# -----------------------
# SYMBOLS & INTERVALS
# -----------------------
symbols = [
    "BTCUSDT","ETHUSDT","SOLUSDT","LTCUSDT","AVAXUSDT",
    "ADAUSDT","ENSUSDT","XRPUSDT","ALGOUSDT","ETCUSDT",
    "SUIUSDT","LINKUSDT"
]

intervals = ["5min", "15min"]

# -----------------------
# LAST HIT STATUS
# -----------------------
last_status = {}

# -----------------------
# FETCH KLINE (بهینه‌تر)
# -----------------------
def get_kline(symbol, interval):
    try:
        url = f"https://api.coinex.com/v1/market/kline?market={symbol}&type={interval}&limit=50"
        resp = requests.get(url, timeout=8)
        data = resp.json()
        if data.get("code") != 0:
            return None
        return [float(c[4]) for c in data["data"]]
    except:
        return None

# -----------------------
# CHECK PRICES LOOP
# -----------------------
def check_prices():
    while True:
        for symbol in symbols:
            for interval in intervals:

                closes = get_kline(symbol, interval)
                if not closes or len(closes) < 50:
                    continue

                last_close = closes[-1]
                prev_close = closes[-2]
                ema = ema50(closes)

                key = f"{symbol}_{interval}"
                last_hit = last_status.get(key)
                message = None

                # برخورد رو به بالا
                if prev_close < ema <= last_close:
                    if last_hit != "up":
                        message = (
                            f"🔼 {symbol}\n"
                            f"برخورد EMA50 رو به بالا ({interval})\n"
                            f"قیمت: {last_close}"
                        )
                        last_status[key] = "up"

                # برخورد رو به پایین
                elif prev_close > ema >= last_close:
                    if last_hit != "down":
                        message = (
                            f"🔽 {symbol}\n"
                            f"برخورد EMA50 رو به پایین ({interval})\n"
                            f"قیمت: {last_close}"
                        )
                        last_status[key] = "down"

                # ارسال پیام اگر تغییر بود
                if message:
                    print(message)
                    try:
                        bot.send_message(chat_id=CHAT_ID, text=message)
                    except Exception as e:
                        print("Telegram error:", e)

        time.sleep(60)  # چک هر ۱ دقیقه (بهترین حالت)

# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8000)).start()
    check_prices()
