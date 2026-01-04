import random
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ================= НАСТРОЙКИ =================
TOKEN = "PASTE_YOUR_REAL_TOKEN_HERE"

FREE_LIMIT = 5

PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY",
    "AUDUSD", "USDCHF", "USDCAD"
]

user_limits = {}

# ================= SIGNAL =================
def generate_signal():
    pair = random.choice(PAIRS)
    entry = round(random.uniform(1.1000, 1.1500), 4)

    if random.choice([True, False]):
        direction = "BUY 📈"
        tp = round(entry + 0.0050, 4)
        sl = round(entry - 0.0030, 4)
    else:
        direction = "SELL 📉"
        tp = round(entry - 0.0050, 4)
        sl = round(entry + 0.0030, 4)

    return (
        f"📊 TRADING SIGNAL\n\n"
        f"Pair: {pair}\n"
        f"Type: {direction}\n\n"
        f"Entry: {entry}\n"
        f"TP: {tp}\n"
        f"SL: {sl}\n\n"
        f"⚠️ Not financial advice"
    )

# ================= /start =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Получить сигнал", callback_data="signal")]
    ])

    await update.message.reply_text(
        "👋 Привет, брат!\n\n"
        "Нажми кнопку ниже и получи сигнал 👇",
        reply_markup=keyboard
    )

# ================= CALLBACK =================
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    today = date.today()

    if user_id not in user_limits or user_limits[user_id]["date"] != today:
        user_limits[user_id] = {"date": today, "count": 0}

    if user_limits[user_id]["count"] >= FREE_LIMIT:
        await query.message.reply_text("❌ Лимит на сегодня исчерпан")
        return

    user_limits[user_id]["count"] += 1
    await query.message.reply_text(generate_signal())

# ================= MAIN =================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(signal, pattern="signal"))

    print("🚀 BOT RUNNING")
    app.run_polling()

if __name__ == "__main__":
    main()



