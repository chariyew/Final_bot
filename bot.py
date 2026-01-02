import random
import asyncio
import logging
from datetime import date, datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ========== НАСТРОЙКИ ==========
TELEGRAM_TOKEN = "7981684997:AAEKMuYLDKYIxenSZgSJ39mfwAJPOLS2_fY"   # ВСТАВЬ СВОЙ ТОКЕН
CHANNEL_USERNAME = "@nejim_signals"        # ТВОЙ КАНАЛ
ADMIN_ID = 8039171205                      # ТВОЙ ID

FREE_LIMIT = 5
AUTO_SIGNAL_INTERVAL = 300  # 5 минут
ANTISPAM_SECONDS = 5

PAIRS = [
    "AUDCAD", "EURUSD", "USDCHF", "CADJPY", "CHFJPY",
    "EURJPY", "AUDUSD", "AUDJPY", "EURCAD", "EURGBP",
    "GBPUSD", "GBPCAD", "EURAUD", "GBPCHF", "AUDCHF"
]

premium_users = set()
user_signals = {}
user_last_click = {}
known_users = set()

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

# ========== КРАСИВОЕ МЕНЮ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    known_users.add(user.id)

    keyboard = [
        [InlineKeyboardButton("📊 Получить сигнал", callback_data="signal")],
        [InlineKeyboardButton("💎 Купить Premium", callback_data="buy_premium")],
        [InlineKeyboardButton("📢 Наш канал", url="https://t.me/nejim_signals")]
    ]

    text = (
        "👋 Привет!\n\n"
        "🔥 FREE — 5 сигналов в день\n"
        "💎 PREMIUM — без лимита\n\n"
        "Нажми кнопку ниже, чтобы получить сигнал 👇"
    )

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ========== АНТИСПАМ ==========
def is_spam(user_id):
    now = datetime.utcnow()
    last = user_last_click.get(user_id)
    if last and now - last < timedelta(seconds=ANTISPAM_SECONDS):
        return True
    user_last_click[user_id] = now
    return False

# ========== СИГНАЛ ПО КНОПКЕ ==========
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # антиспам
    if is_spam(user_id):
        await query.message.reply_text("⏳ Подожди пару секунд...")
        return

    # проверка подписки
    if not await is_subscribed(user_id, context):
        await query.message.reply_text(
            "❌ Подпишись на канал!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Подписаться", url="https://t.me/nejim_signals")]
            ])
        )
        return

    # админ без лимита
    if user_id != ADMIN_ID:
        today = date.today()
        if user_id not in user_signals or user_signals[user_id]["date"] != today:
            user_signals[user_id] = {"date": today, "count": 0}

        if user_signals[user_id]["count"] >= FREE_LIMIT:
            await query.message.reply_text("❌ Лимит 5 сигналов. 💎 Premium — без лимита")
            return

        user_signals[user_id]["count"] += 1

    # отправка сигнала
    text, image = generate_signal()
    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=open(image, "rb"),
        caption=text
    )

# ========== КУПИТЬ PREMIUM ==========
async def buy_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = (
        "💎 PREMIUM ДОСТУП\n\n"
        "Чтобы оформить Premium, перейди в наш официальный канал:\n"
        "👉 https://t.me/nejim_signals\n\n"
        "В канале есть вся информация, условия и поддержка."
    )

    keyboard = [
        [InlineKeyboardButton("🔥 Открыть Premium канал", url="https://t.me/nejim_signals")]
    ]

    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ========== PREMIUM КОМАНДА ==========
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

# ========== СТАТИСТИКА ==========
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Нет доступа")
        return

    total_users = len(known_users)
    total_premium = len(premium_users)

    today = date.today()
    total_signals_today = sum(
        data["count"] for data in user_signals.values() if data["date"] == today
    )

    text = (
        "📊 Статистика\n\n"
        f"👥 Пользователей: {total_users}\n"
        f"💎 Premium: {total_premium}\n"
        f"📨 Сигналов сегодня: {total_signals_today}"
    )

    await update.message.reply_text(text)

# ========== АВТОСИГНАЛЫ 24/7 ==========
async def auto_signals(app):
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
            logger.error(f"Auto-signal error: {e}")

        await asyncio.sleep(AUTO_SIGNAL_INTERVAL)

# ========== MAIN ==========
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_premium", add_premium))
    app.add_handler(CommandHandler("stats", stats))

    app.add_handler(CallbackQueryHandler(signal, pattern="^signal$"))
    app.add_handler(CallbackQueryHandler(buy_premium_callback, pattern="^buy_premium$"))

    async def on_start(app):
        asyncio.create_task(auto_signals(app))

    app.post_init = on_start

    print("🚀 BOT FULL POWER STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()



