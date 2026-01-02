import asyncio
import logging
from datetime import datetime, timedelta

from telegram import Bot

# ========== НАСТРОЙКИ ==========
TELEGRAM_TOKEN = "7981684997:AAEKMuYLDKYIxenSZgSJ39mfwAJPOLS2_fY"
ADMIN_ID = 8039171205

CHECK_INTERVAL = 5
DOGON_DELAY = 300

# ========== 25 ПАР ==========
PAIRS = [
    "AUDCAD", "EURUSD", "USDCHF", "CADJPY", "CHFJPY",
    "EURJPY", "AUDUSD", "AUDJPY", "EURCAD", "EURGBP",
    "GBPUSD", "GBPCAD", "EURAUD", "GBPCHF", "AUDCHF",
    "NZDUSD", "USDJPY", "EURCHF", "AUDNZD", "NZDCAD",
    "NZDCHF", "CADCHF", "GBPJPY", "EURNZD", "USDHKD"
]

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
        f"💎 УРОВНЕВОЙ СИГНАЛ\n"
        f"Пара: {pair}\n"
        f"Тип: {'ВЫШЕ' if direction=='UP' else 'НИЖЕ'}\n"
        f"Уровень: {level}\n"
        f"Догон: 1/3\n"
    )

    photo = PHOTO_UP if direction == "UP" else PHOTO_DOWN

    await bot.send_message(chat_id=ADMIN_ID, text=text)

    current_signal = Signal(pair, direction, level)

# ========== ДОГОН ==========
async def send_dogon():
    global current_signal

    current_signal.dogon += 1

    if current_signal.dogon > 3:
        await bot.send_message(ADMIN_ID, "❌ Минус. 3 догона не сработали.")
        current_signal.active = False
        return

    text = (
        f"🔥 ДОГОН {current_signal.dogon}/3\n"
        f"Пара: {current_signal.pair}\n"
        f"Тип: {'ВЫШЕ' if current_signal.direction=='UP' else 'НИЖЕ'}\n"
        f"Уровень: {current_signal.level}\n"
    )

    await bot.send_message(ADMIN_ID, text)

# ========== ПРОВЕРКА ==========
async def check_result():
    global current_signal

    if not current_signal or not current_signal.active:
        return

    # завтра заменим на реальную проверку
    await send_dogon()

# ========== МОНИТОРИНГ ==========
async def monitor():
    await bot.send_message(ADMIN_ID, "🚀 Уровневой бот запущен 24/7")

    global current_signal

    while True:
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
