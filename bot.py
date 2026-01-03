# ================== IMPORTS ==================
import os
import random
import asyncio
import threading
from datetime import date
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ================== CONFIG ==================
TELEGRAM_TOKEN = os.getenv("7981684997:AAFMrrmmiAY9gTeH1zWoq_A0FX19cCugLKw")  # ОБЯЗАТЕЛЬНО через env
CHANNEL_ID = -1003531475408                   # ТВОЙ CHAT_ID КАНАЛА
ADMIN_ID = 8039171205

FREE_LIMIT = 5
AUTO_SIGNAL_INTERVAL = 300  # 5 минут

PAIRS = [
    "AUDCAD", "EURUSD", "USDCHF", "CADJPY", "CHFJPY",
    "EURJPY", "AUDUSD", "AUDJPY", "EURCAD", "EURGBP",
    "GBPUSD", "GBPCAD", "EURAUD", "GBPCHF", "AUDCHF"
]

premium_users = set()
user_signals = {}

# ================== DUMMY SERVER (Fly / Render) ==================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), DummyHandler).serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# ================== SIGNAL GENERATOR ==================
def generate_signal():
    pair = random.choice(PAIRS)
    entry = round(random.uniform(1.1000, 1.1500), 4)

    if random.choice([True, False]):
        direction = "BUY 📈"
        tp = round(entry + 0.0060, 4)
        sl = round(entry - 0.0030, 4)
    else:
        direction = "SELL 📉"
        tp = round(entry - 0.0060, 4)
        sl = round(entry + 0.0030, 4)

    return (
        f"📊 TRADING SIGNAL\n\n"
        f"Пара: {pair}\n"
        f"Тип: {direction}\n\n"
        f"Вход: {entry}\n"
        f"TP: {tp}\n"
        f"SL: {sl}\n\n"
        f"⚠️ Не финансовый совет"
    )

# ================== /start ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Получить сигнал", callback_data="signal")],
        [InlineKeyboardButton("📢 Канал", url="https://t.me/nejim_signals")]
    ]

    await update.message.reply_text(
        "👋 Привет, брат!\n\n"
        "🔥 FREE — 5 сигналов в день\n"
        "💎 PREMIUM — без лимита\n\n"
        "Выбирай 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== MANUAL SIGNAL ==================
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    today = date.today()

    if user_id not in user_signals or user_signals[user_id]["date"] != today:
        user_signals[user_id] = {"date": today, "count": 0}

    if user_id not in premium_users and user_signals[user_id]["count"] >= FREE_LIMIT:
        await query.message.reply_text("❌ Лимит 5 сигналов. 💎 Premium — без лимита")
        return

    user_signals[user_id]["count"] += 1
    await query.message.reply_text(generate_signal())

# ================== PREMIUM ==================
async def add_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Нет доступа")
        return

    try:
        uid = int(context.args[0])
        premium_users.add(uid)
        await update.message.reply_text(f"✅ {uid} теперь PREMIUM")
    except:
        await update.message.reply_text("Используй: /add_premium USER_ID")

# ================== AUTO SIGNALS 24/7 ==================
async def auto_signals(app: Application):
    await asyncio.sleep(15)
    while True:
        try:
            await app.bot.send_message(
                chat_id=CHANNEL_ID,
                text=generate_signal()
            )
        except Exception as e:
            print("AUTO ERROR:", e)

        await asyncio.sleep(AUTO_SIGNAL_INTERVAL)

# ================== MAIN ==================
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_premium", add_premium))
    app.add_handler(CallbackQueryHandler(signal, pattern="signal"))

    async def on_start(app: Application):
        asyncio.create_task(auto_signals(app))

    app.post_init = on_start

    print("🚀 BOT FULL POWER 24/7 STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()



