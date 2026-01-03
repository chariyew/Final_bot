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
        tp = round(entry + 0.0060, 4)
        sl = round(entry - 0.0030, 4)
    else:
        direction = "SELL 📉"
        tp = round(entry - 0.0060, 4)
        sl = round(entry + 0.0030, 4)
# ========== УРОВНИ MAX/MIN ==========
LEVELS = {
    "EURUSD": {"MAX": 1.1500, "MIN": 1.1000},
    "GBPUSD": {"MAX": 1.3200, "MIN": 1.2700},
    "USDCHF": {"MAX": 0.9200, "MIN": 0.8800},
    "USDJPY": {"MAX": 152.000, "MIN": 145.000},
    "AUDUSD": {"MAX": 0.6900, "MIN": 0.6500},
    "NZDUSD": {"MAX": 0.6400, "MIN": 0.6000},
    "EURJPY": {"MAX": 165.000, "MIN": 158.000},
    "GBPJPY": {"MAX": 190.000, "MIN": 183.000},
    "EURGBP": {"MAX": 0.8800, "MIN": 0.8400},
    "EURAUD": {"MAX": 1.7000, "MIN": 1.6400},
    "AUDCAD": {"MAX": 0.9200, "MIN": 0.8800},
    "AUDJPY": {"MAX": 102.000, "MIN": 96.000},
    "AUDNZD": {"MAX": 1.1200, "MIN": 1.0600},
    "AUDCHF": {"MAX": 0.6200, "MIN": 0.5800},
    "NZDCAD": {"MAX": 0.8600, "MIN": 0.8200},
    "NZDCHF": {"MAX": 0.5800, "MIN": 0.5400},
    "CADJPY": {"MAX": 115.000, "MIN": 109.000},
    "CADCHF": {"MAX": 0.6900, "MIN": 0.6500},
    "CHFJPY": {"MAX": 175.000, "MIN": 168.000},
    "EURCAD": {"MAX": 1.5200, "MIN": 1.4700},
    "EURCHF": {"MAX": 0.9900, "MIN": 0.9500},
    "GBPCAD": {"MAX": 1.7600, "MIN": 1.7100},
    "GBPCHF": {"MAX": 1.1800, "MIN": 1.1400},
    "EURNZD": {"MAX": 1.8400, "MIN": 1.7800},
    "USDHKD": {"MAX": 7.8500, "MIN": 7.8000},
}

# ========== КАРТИНКИ ==========
PHOTO_UP = "FILE_ID_VYSHE"
PHOTO_DOWN = "FILE_ID_NIZHE"

bot = Bot(token=TELEGRAM_TOKEN)

# ========== ЗАГЛУШКА ЦЕНЫ ==========
async def get_price(pair):
    return LEVELS[pair]["MIN"]  # завтра заменим на TradingView

# ========== СТРУКТУРА СИГНАЛА ==========
class Signal:
    def __init__(self, pair, direction, level):
        self.pair = pair
        self.direction = direction
        self.level = level
        self.dogon = 0
        self.active = True
        self.entry_time = datetime.utcnow()

current_signal = None

# ========== ОТПРАВКА СИГНАЛА ==========
async def send_signal(pair, direction, level):
    global current_signal

    text = (
        f"📊 TRADING SIGNAL\n\n"
        f"💎 УРОВНЕВОЙ СИГНАЛ\n"
        f"Пара: {pair}\n"
        f"Тип: {direction}\n\n"
        f"Вход: {entry}\n"
        f"TP: {tp}\n"
        f"SL: {sl}\n\n"
        f"⚠️ Не финансовый совет"
        f"Тип: {'ВЫШЕ' if direction=='UP' else 'НИЖЕ'}\n"
        f"Уровень: {level}\n"
        f"Догон: 1/3\n"
    )
    return text

# ========== ПРОВЕРКА ПОДПИСКИ ==========
async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ========== МЕНЮ ==========
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
    photo = PHOTO_UP if direction == "UP" else PHOTO_DOWN

    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

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

    if is_spam(user_id):
        await query.message.reply_text("⏳ Подожди пару секунд...")
        return
    await bot.send_message(chat_id=ADMIN_ID, text=text)

    if not await is_subscribed(user_id, context):
        await query.message.reply_text(
            "❌ Подпишись на канал!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Подписаться", url="https://t.me/nejim_signals")]
            ])
        )
        return

    if user_id != ADMIN_ID:
        today = date.today()
        if user_id not in user_signals or user_signals[user_id]["date"] != today:
            user_signals[user_id] = {"date": today, "count": 0}
    current_signal = Signal(pair, direction, level)

        if user_signals[user_id]["count"] >= FREE_LIMIT:
            await query.message.reply_text("❌ Лимит 5 сигналов. 💎 Premium — без лимита")
            return
# ========== ДОГОН ==========
async def send_dogon():
    global current_signal

        user_signals[user_id]["count"] += 1
    current_signal.dogon += 1

    text = generate_signal()
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text
    )

# ========== PREMIUM ==========
async def buy_premium_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if current_signal.dogon > 3:
        await bot.send_message(ADMIN_ID, "❌ Минус. 3 догона не сработали.")
        current_signal.active = False
        return

    text = (
        "💎 PREMIUM ДОСТУП\n\n"
        "Чтобы оформить Premium, перейди в наш официальный канал:\n"
        "👉 https://t.me/nejim_signals\n\n"
        "В канале есть вся информация, условия и поддержка."
        f"🔥 ДОГОН {current_signal.dogon}/3\n"
        f"Пара: {current_signal.pair}\n"
        f"Тип: {'ВЫШЕ' if current_signal.direction=='UP' else 'НИЖЕ'}\n"
        f"Уровень: {current_signal.level}\n"
    )

    keyboard = [
        [InlineKeyboardButton("🔥 Открыть Premium канал", url="https://t.me/nejim_signals")]
    ]
    await bot.send_message(ADMIN_ID, text)

    await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
# ========== ПРОВЕРКА ==========
async def check_result():
    global current_signal

# ========== СТАТИСТИКА ==========
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Нет доступа")
    if not current_signal or not current_signal.active:
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
    # завтра заменим на реальную проверку
    await send_dogon()

    await update.message.reply_text(text)
# ========== МОНИТОРИНГ ==========
async def monitor():
    await bot.send_message(ADMIN_ID, "🚀 Уровневой бот запущен 24/7")

# ========== АВТОСИГНАЛЫ 24/7 ==========
async def auto_signals(app):
    await asyncio.sleep(5)
    global current_signal

    while True:
        try:
            text = generate_signal()

            await app.bot.send_message(
                chat_id=CHANNEL_USERNAME,
                text=text,
                disable_notification=False
            )

            print("Автосигнал отправлен!")

        except Exception as e:
            logger.error(f"Auto-signal error: {e}")

        await asyncio.sleep(AUTO_SIGNAL_INTERVAL)

# ========== MAIN ==========
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
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

        for pair in PAIRS:
            price = await get_price(pair)
            max_l = LEVELS[pair]["MAX"]
            min_l = LEVELS[pair]["MIN"]

            if not current_signal or not current_signal.active:
                if price >= max_l:
                    await send_signal(pair, "DOWN", max_l)
                elif price <= min_l:
                    await send_signal(pair, "UP", min_l)
            else:
                if datetime.utcnow() - current_signal.entry_time >= timedelta(seconds=DOGON_DELAY):
                    current_signal.entry_time = datetime.utcnow()
                    await check_result()

        await asyncio.sleep(CHECK_INTERVAL)

asyncio.run(monitor())



