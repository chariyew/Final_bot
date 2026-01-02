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
TELEGRAM_TOKEN = "7981684997:AAEKMuYLDKYIxenSZgSJ39mfwAJPOLS2_fY"  # ВСТАВЬ СВОЙ ТОКЕН
CHANNEL_USERNAME = "@nejim_signals"       # ТВОЙ КАНАЛ
ADMIN_ID = 8039171205                     # ТВОЙ ID

FREE_LIMIT = 5
AUTO_SIGNAL_INTERVAL = 300  # 5 минут
ANTISPAM_SECONDS = 5        # антиспам на кнопку сигнала

PAIRS = [
    "AUDCAD", "EURUSD", "USDCHF", "CADJPY", "CHFJPY",
    "EURJPY", "AUDUSD", "AUDJPY", "EURCAD", "EURGBP",
    "GBPUSD", "GBPCAD", "EURAUD", "GBPCHF", "AUDCHF"
]

premium_users = set()
user_signals = {}        # user_id -> {"date": date, "count": int}
user_last_click = {}     # user_id -> datetime
known_users = set()      # все, кто писал боту хоть раз

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
    except Exception as e:
        logger.warning(f"is_subscribed error for {user_id}: {e}")
        return False

# ========== КРАСИВОЕ МЕНЮ /start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    known_users.add(user.id)

    keyboard = [
        [InlineKeyboardButton("📊 Получить сигнал", callback_data="signal")],
        [InlineKeyboardButton("💎 Купить Premium", callback_data="buy_premium")],
        [
            InlineKeyboardButton("📢 Наш канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"),
            InlineKeyboardButton("🧑‍💻 Поддержка", url="https://t.me/your_support_username")
        ]
    ]

    text = (
        "👋 Привет!\n\n"
        "🔥 FREE — 5 сигналов в день\n"
        "💎 PREMIUM — без лимита и без ожидания\n\n"
        "Нажми кнопку ниже, чтобы получить сигнал 👇"
    )

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    logger.info(f"/start от {user.id} (@{user.username})")

# ========== АНТИСПАМ ==========
def is_spam(user_id: int) -> bool:
    now = datetime.utcnow()
    last = user_last_click.get(user_id)
    if last is None:
        user_last_click[user_id] = now
        return False
    if now - last < timedelta(seconds=ANTISPAM_SECONDS):
        return True
    user_last_click[user_id] = now
    return False

# ========== РУЧНОЙ СИГНАЛ ==========
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    known_users.add(user_id)

    # антиспам
    if is_spam(user_id):
        await query.message.reply_text("⏳ Не так быстро, подожди пару секунд...")
        return

    # проверка подписки
    if not await is_subscribed(user_id, context):
        await query.message.reply_text(
            "❌ Подпишись на канал, чтобы получать сигналы:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]
            ])
        )
        return

    # лимит
    today = date.today()
    if user_id not in user_signals or user_signals[user_id]["date"] != today:
        user_signals[user_id] = {"date": today, "count": 0}

    if user_id not in premium_users and user_signals[user_id]["count"] >= FREE_LIMIT:
        await query.message.reply_text("❌ Лимит 5 сигналов. 💎 Premium — без лимита")
        logger.info(f"Лимит исчерпан у {user_id}")
        return

    user_signals[user_id]["count"] += 1

    text, image = generate_signal()
    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=open(image, "rb"),
        caption=text
    )
    logger.info(f"Сигнал отправлен пользователю {user_id}")

# ========== КНОПКА "КУПИТЬ PREMIUM" ==========
async def buy_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    known_users.add(user.id)

    text = (
        "💎 PREMIUM ДОСТУП\n\n"
        "✅ Без лимита сигналов\n"
        "✅ Приоритетные сигналы\n"
        "✅ Поддержка 1:1\n\n"
        "Чтобы купить Premium, напиши сюда:\n"
        "👉 @your_support_username"
    )

    await query.message.reply_text(text)
    logger.info(f"Пользователь {user.id} нажал 'Купить Premium'")

# ========== PREMIUM КОМАНДА ==========
async def add_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Нет доступа")
        return

    try:
        user_id = int(context.args[0])
        premium_users.add(user_id)
        await update.message.reply_text(f"✅ {user_id} теперь PREMIUM")
        logger.info(f"Добавлен PREMIUM: {user_id}")
    except Exception as e:
        await update.message.reply_text("Используй: /add_premium USER_ID")
        logger.warning(f"Ошибка add_premium: {e}")

# ========== СТАТИСТИКА ДЛЯ АДМИНА ==========
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Нет доступа")
        return

    total_users = len(known_users)
    total_premium = len(premium_users)

    today = date.today()
    total_signals_today = sum(
        data["count"] for uid, data in user_signals.items() if data["date"] == today
    )

    text = (
        "📊 Статистика бота\n\n"
        f"👥 Пользователей всего: {total_users}\n"
        f"💎 Premium: {total_premium}\n"
        f"📨 Сигналов сегодня: {total_signals_today}\n"
    )

    await update.message.reply_text(text)
    logger.info("Админ запросил статистику")

# ========== АДМИН-ПАНЕЛЬ ==========
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Нет доступа")
        return

    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("💎 Список Premium (кол-во)", callback_data="admin_premium")],
    ]

    await update.message.reply_text(
        "🛠 Админ-панель",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id != ADMIN_ID:
        await query.message.reply_text("❌ Нет доступа")
        return

    if query.data == "admin_stats":
        today = date.today()
        total_users = len(known_users)
        total_premium = len(premium_users)
        total_signals_today = sum(
            data["count"] for uid, data in user_signals.items() if data["date"] == today
        )
        text = (
            "📊 Статистика бота\n\n"
            f"👥 Пользователей всего: {total_users}\n"
            f"💎 Premium: {total_premium}\n"
            f"📨 Сигналов сегодня: {total_signals_today}\n"
        )
        await query.message.reply_text(text)
    elif query.data == "admin_premium":
        text = (
            f"💎 Premium пользователей: {len(premium_users)}\n"
            "ID можно хранить отдельно, если нужно детально."
        )
        await query.message.reply_text(text)

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
            logger.info("Автосигнал отправлен в канал")
        except Exception as e:
            logger.error(f"Auto-signal error: {e}")

        await asyncio.sleep(AUTO_SIGNAL_INTERVAL)

# ========== MAIN ==========
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_premium", add_premium))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("admin", admin_panel))

    app.add_handler(CallbackQueryHandler(signal, pattern="^signal$"))
    app.add_handler(CallbackQueryHandler(buy_premium_callback, pattern="^buy_premium$"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))

    async def on_start(app: Application):
        asyncio.create_task(auto_signals(app))

    app.post_init = on_start

    logger.info("🚀 BOT FULL POWER 24/7 STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()
