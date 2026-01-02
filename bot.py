import os
import random
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_USERNAME = "@nejim_signals"
ADMIN_ID = 8039171205
FREE_LIMIT = 5

PAIRS = [
    "AUDCAD","EURUSD","USDCHF","CADJPY","CHFJPY",
    "EURJPY","AUDUSD","AUDJPY","EURCAD","EURGBP",
    "GBPUSD","GBPCAD","EURAUD","GBPCHF","AUDCHF"
]

premium_users = set()
user_signals = {}

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

async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member","administrator","creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Получить сигнал", callback_data="signal")],
        [InlineKeyboardButton("📢 Наш канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]
    ]
    await update.message.reply_text(
        "👋 Привет, брат!\n\n"
        "🔥 FREE — 5 сигналов в день\n"
        "💎 PREMIUM — без лимита\n\n"
        "Выбирай 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not await is_subscribed(user_id, context):
        await query.message.reply_text("❌ Подпишись на канал")
        return

    today = date.today()
    user_signals.setdefault(user_id, {"date": today, "count": 0})

    if user_signals[user_id]["date"] != today:
        user_signals[user_id] = {"date": today, "count": 0}

    if user_id not in premium_users and user_signals[user_id]["count"] >= FREE_LIMIT:
        await query.message.reply_text("❌ Лимит исчерпан")
        return

    user_signals[user_id]["count"] += 1
    await query.message.reply_text(generate_signal())

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(signal, pattern="signal"))
    print("🚀 BOT RUNNING 24/7")
    app.run_polling()

if __name__ == "__main__":
    main()
