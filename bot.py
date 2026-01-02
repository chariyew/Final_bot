import random
import asyncio
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ========== НАСТРОЙКИ ==========
TELEGRAM_TOKEN = "7981684997:AAEKMuYLDKYIxenSZgSJ39mfwAJPOLS2_fY"
CHANNEL_USERNAME = "@nejim_signals"
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

# ========== ГЕНЕРАЦИЯ СИГНАЛА ==========
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

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ========== /start ==========
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

# ========== РУЧНОЙ СИГНАЛ ==========
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not await is_subscribed(user_id, context):
        await query.message.reply_text(
            "❌ Подпишись на канал!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Подписаться", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]
            ])
        )
        return

    today = date.today()
    if user_id not in user_signals or user_signals[user_id]["date"] != today:
        user_signals[user_id] = {"date": today, "count": 0}

    if user_id not in premium_users and user_signals[user_id]["count"] >= FREE_LIMIT:
        await query.message.reply_text("❌ Лимит 5 сигналов. 💎 Premium — без лимита")
        return

    user_signals[user_id]["count"] += 1
    text, image = generate_signal()

    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=open(image, "rb"),
        caption=text
    )

# ========== PREMIUM ==========
async def add_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Нет доступа")
        return

    try:
        user_id = int(context.args[0])
        premium_users.add(user_id)
        await update.message.reply_text(f"✅ {user_id} теперь PREMIUM")
    except:
        await update.message.reply_text("Используй: /add_premium USER_ID")

# ========== АВТОСИГНАЛЫ 24/7 ==========
async def auto_signals(app: Application):
    await asyncio.sleep(10)
    while True:
        try:
            text, image = generate_signal()
            await app.bot.send_photo(
                chat_id=CHANNEL_USERNAME,
                photo=open(image, "rb"),
                caption=text
            )
        except Exception as e:
            print("Auto-signal error:", e)

        await asyncio.sleep(AUTO_SIGNAL_INTERVAL)

# ========== MAIN ==========
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
