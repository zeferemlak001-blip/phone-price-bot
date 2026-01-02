import os
import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from statistics import mean, median
import re
import time
from keep_alive import keep_alive # Render üçün botu canlı saxlamaq

# Telegram token
BOT_TOKEN = os.getenv("7612014580:AAHFDvz9I07K6-My__qJ9-OHPVwpvVJ_pss")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
"AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
}
FX = {"USD": 1.7, "EUR": 1.85, "AZN": 1.0}


def normalize_price(text):
text = text.replace("\xa0", " ").replace("₼", "AZN").strip()
currency = "AZN"
if "$" in text or "USD" in text:
currency = "USD"
if "€" in text or "EUR" in text:
currency = "EUR"
nums = re.findall(r"[0-9]+", text)
if not nums:
return 0
val = float("".join(nums))
return val * FX.get(currency, 1.0)


def search_tapaz(model):
url = f"https://tap.az/elanlar?query={model.replace(' ', '+')}"
r = requests.get(url, headers=HEADERS, timeout=10)
soup = BeautifulSoup(r.text, "lxml")
prices = []
for p in soup.select(".products-i__price"):
val = normalize_price(p.text)
if 100 < val < 10000:
prices.append(val)
return prices


def search_lalafo(model):
url = f"https://lalafo.az/baku/ads?q={model.replace(' ', '+')}"
r = requests.get(url, headers=HEADERS, timeout=10)
soup = BeautifulSoup(r.text, "lxml")
prices = []
for p in soup.select(".ListingCell-price"):
val = normalize_price(p.text)
if 100 < val < 10000:
prices.append(val)
return prices


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
"Salam! 📱 Mən sənin telefon qiyməti botunam.\n"
"Sadəcə model adını yaz, məsələn:\n👉 iPhone 15 Pro"
)


async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.message.text.strip()
await update.message.reply_text("🔍 Axtarılır, zəhmət olmasa gözləyin...")

prices = []
try:
prices += search_tapaz(query)
time.sleep(2)
prices += search_lalafo(query)
except Exception as e:
logger.error(f"Error: {e}")
await update.message.reply_text(f"⚠️ Xəta baş verdi: {e}")
return

if not prices:
await update.message.reply_text("😔 Uyğun elan tapılmadı.")
return

avg_price = round(mean(prices), 2)
med_price = round(median(prices), 2)
msg = (
f"📱 Model: {query}\n"
f"💰 Orta qiymət: {avg_price} AZN\n"
f"⚖️ Median qiymət: {med_price} AZN\n"
f"🔎 {len(prices)} elan analiz edildi."
)
await update.message.reply_text(msg)


def main():
keep_alive()
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))
print("✅ Bot Render-də işləyir. Telegram-da yoxla!")
app.run_polling()


if __name__ == "__main__":
main()
