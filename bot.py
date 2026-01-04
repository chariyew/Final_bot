import asyncio
import random
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ========= НАСТРОЙКИ =========
TELEGRAM_TOKEN = "7981684997:AAFMrrmmiAY9gTeH1zWoq_A0FX19cCugLKw"
CHANNEL_ID = -1003531475408   # твой канал
FREE_LIMIT = 5
AUTO_SIGNAL_INTERVAL = 300  # 5 минут

PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
    "EURJPY", "GBPJPY", "USDCAD", "USDCHF"
]

user_signals = {}
premium_users = set()

print("🔥 NEJIM SIGNAL BOT VERSION 2 STARTED 🔥")

# ========= ГЕНЕРАЦИЯ СИГНАЛА =========
def generate_signal():
    pair = random.choice(PAIRS)
    entry = round(random.uniform(1.1000, 1.1500), 4)

    if random.choice([True, False]):
        direction = "BUY 📈"
        image = "above.jpg"
        tp = round(entry + 0.0060, 4)
        sl = round(entry - 0.0030, 4)
    else:
        direction = "SELL 📉"
        image = "below.jpg"
        tp = round(entry - 0.0060, 4)
        sl = round(entry + 0.0030, 4)

    text = (
        f"📊 TRADING SIGNAL\n\n"
        f"Пара: {pair}\n"
        f"Тип: {direction}\n\n"
        f"Вход: {entry}\n"
        f"TP: {tp}\n"
        f"SL: {sl}\n\n"
        f"⚠️ Не финансовый совет"
    )
    return text, image

# ========= /start =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Получить сигнал", callback_data="signal")],
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/nejim_signals")]
    ]

    await update.message.reply_text(
        "🔥 NEJIM SIGNAL BOT ACTIVE 🔥\n\n"
        "FREE — 5 сигналов в день\n"
        "PREMIUM — без лимита\n\n"
        "Выбирай 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========= РУЧНОЙ СИГНАЛ =========
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    today = date.today()

    if user_id not in user_signals or user_signals[user_id]["date"] != today:
        user_signals[user_id] = {"date": today, "count": 0}

    if user_id not in premium_users and user_signals[user_id]["count"] >= FREE_LIMIT:
        await query.message.reply_text("❌ Лимит 5 сигналов в день")
        return

    user_signals[user_id]["count"] += 1
    text, image = generate_signal()

    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=open(image, "rb"),
        caption=text
    )

# ========= АВТОСИГНАЛЫ В КАНАЛ =========
async def auto_signals(app: Application):
    await asyncio.sleep(10)
    while True:
        try:
            text, image = generate_signal()
            await app.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=open(image, "rb"),
                caption=text
            )
        except Exception as e:
            print("Auto-signal error:", e)

        await asyncio.sleep(AUTO_SIGNAL_INTERVAL)

# ========= MAIN =========
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(signal, pattern="signal"))

    asyncio.create_task(auto_signals(app))

    print("🚀 BOT FULL POWER 24/7 RUNNING")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
