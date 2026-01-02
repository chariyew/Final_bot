import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from telegram import Bot

# ================== НАСТРОЙКИ ==================

TELEGRAM_TOKEN = "7981684997:AAEKMuYLDKYIxenSZgSJ39mfwAJPOLS2_fY"
ADMIN_ID = 8039171205  # твой Telegram ID

CHECK_INTERVAL = 5      # как часто проверять цену (сек)
DOGON_DELAY = 300       # задержка между входами/догоном (сек)

# Картинки сигналов (file_id из Telegram)
PHOTO_UP = "FILE_ID_VYSHE"    # картинка ВЫШЕ
PHOTO_DOWN = "FILE_ID_NIZHE"  # картинка НИЖЕ

# ================== СПИСОК 25 ПАР ==================

PAIRS = [
    "AUDCAD", "EURUSD", "USDCHF", "CADJPY", "CHFJPY",
    "EURJPY", "AUDUSD", "AUDJPY", "EURCAD", "EURGBP",
    "GBPUSD", "GBPCAD", "EURAUD", "GBPCHF", "AUDCHF",
    "NZDUSD", "USDJPY", "EURCHF", "AUDNZD", "NZDCAD",
    "NZDCHF", "CADCHF", "GBPJPY", "EURNZD", "USDHKD"
]

# ================== УРОВНИ MAX/MIN ==================

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

# ================== ЛОГИ ==================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)

# ================== ЗАГЛУШКА ЦЕНЫ ==================
# Брат, вот сюда ты потом сам подключишь TradingView.
# Сейчас — просто пример, чтобы структура работала.

async def get_price(pair: str) -> Optional[float]:
    """
    СЮДА ПОДКЛЮЧИШЬ TRADINGVIEW:
    - WebSocket / REST
    - вернёшь актуальную цену по паре
    Сейчас — заглушка: возвращаем середину между MAX и MIN.
    """
    levels = LEVELS.get(pair)
    if not levels:
        return None
    return round((levels["MAX"] + levels["MIN"]) / 2, 5)


# ================== СТРУКТУРА СИГНАЛА ==================

class Signal:
    def __init__(self, pair: str, direction: str, level: float):
        self.pair = pair              # "EURUSD"
        self.direction = direction    # "UP" или "DOWN"
        self.level = level            # уровень входа (MAX или MIN)
        self.dogon_step = 1           # текущий догон (1..3)
        self.active = True
        self.entry_time = datetime.utcnow()

    def __repr__(self):
        return f"<Signal {self.pair} {self.direction} {self.level} догон {self.dogon_step}/3>"


current_signal: Optional[Signal] = None


# ================== ОТПРАВКА СИГНАЛА ==================

async def send_signal(pair: str, direction: str, level: float):
    """
    direction: "UP" → ВЫШЕ, "DOWN" → НИЖЕ
    """
    global current_signal

    signal_type = "ВЫШЕ" if direction == "UP" else "НИЖЕ"
    photo = PHOTO_UP if direction == "UP" else PHOTO_DOWN

    text = (
        f"💎 УРОВНЕВОЙ СИГНАЛ\n"
        f"━━━━━━━━━━━━━━\n"
        f"📊 Пара: {pair}\n"
        f"📌 Тип: {signal_type}\n"
        f"💰 Уровень входа: {level}\n"
        f"🔥 Догон: 1/3\n"
        f"━━━━━━━━━━━━━━\n"
        f"⚠️ Не финансовый совет\n"
        f"@nejim_signals"
    )

    current_signal = Signal(pair, direction, level)

    try:
        if PHOTO_UP != "FILE_ID_VYSHE" and PHOTO_DOWN != "FILE_ID_NIZHE":
            await bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=text)
        else:
            await bot.send_message(chat_id=ADMIN_ID, text=text)
    except Exception as e:
        logger.error(f"Ошибка отправки сигнала: {e}")
        await bot.send_message(chat_id=ADMIN_ID, text=text)

    logger.info(f"Отправлен сигнал: {current_signal}")


# ================== ДОГОН ==================

async def send_dogon():
    global current_signal

    if not current_signal or not current_signal.active:
        return

    current_signal.dogon_step += 1

    if current_signal.dogon_step > 3:
        # 3 догона не сработали → минус
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"❌ Минус по {current_signal.pair}. 3 догона не отработали."
        )
        logger.info(f"Минус зафиксирован: {current_signal}")
        current_signal.active = False
        return

    signal_type = "ВЫШЕ" if current_signal.direction == "UP" else "НИЖЕ"
    photo = PHOTO_UP if current_signal.direction == "UP" else PHOTO_DOWN

    text = (
        f"🔥 ДОГОН {current_signal.dogon_step}/3\n"
        f"📊 Пара: {current_signal.pair}\n"
        f"📌 Тип: {signal_type}\n"
        f"💰 Уровень: {current_signal.level}\n"
        f"⚠️ Работаем по уровню, аккуратно."
    )

    try:
        if PHOTO_UP != "FILE_ID_VYSHE" and PHOTO_DOWN != "FILE_ID_NIZHE":
            await bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=text)
        else:
            await bot.send_message(chat_id=ADMIN_ID, text=text)
    except Exception as e:
        logger.error(f"Ошибка отправки догона: {e}")
        await bot.send_message(chat_id=ADMIN_ID, text=text)

    logger.info(f"Отправлен догон: {current_signal}")


# ================== ПРОВЕРКА WIN/LOSS ==================

async def check_result():
    """
    Здесь должна быть реальная проверка WIN/LOSS по цене.
    Сейчас — структура, чтобы ты потом сам дописал.
    """
    global current_signal

    if not current_signal or not current_signal.active:
        return

    price = await get_price(current_signal.pair)
    if price is None:
        return

    win = False

    # Логика:
    # ВЫШЕ (UP): цена должна быть ВЫШЕ уровня
    # НИЖЕ (DOWN): цена должна быть НИЖЕ уровня
    if current_signal.direction == "UP" and price > current_signal.level:
        win = True
    elif current_signal.direction == "DOWN" and price < current_signal.level:
        win = True

    if win:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"✅ WIN по {current_signal.pair} на уровне {current_signal.level} (догон {current_signal.dogon_step}/3)"
        )
        logger.info(f"WIN: {current_signal}")
        current_signal.active = False
    else:
        # LOSS → догон
        logger.info(f"LOSS: {current_signal}, запускаем догон")
        await send_dogon()


# ================== МОНИТОРИНГ УРОВНЕЙ ==================

async def monitor_levels():
    global current_signal

    await bot.send_message(chat_id=ADMIN_ID, text="🚀 Уровневой бот запущен 24/7 по 25 парам.")

    while True:
        try:
            for pair in PAIRS:
                levels = LEVELS.get(pair)
                if not levels:
                    continue

                price = await get_price(pair)
                if price is None:
                    continue

                max_l = levels["MAX"]
                min_l = levels["MIN"]

                # если нет активного сигнала — ищем касание уровней
                if not current_signal or not current_signal.active:
                    # касание MAX → НИЖЕ
                    if price >= max_l:
                        await send_signal(pair, "DOWN", max_l)

                    # касание MIN → ВЫШЕ
                    elif price <= min_l:
                        await send_signal(pair, "UP", min_l)

                else:
                    # если сигнал активен — проверяем по времени, пора ли считать результат
                    if datetime.utcnow() - current_signal.entry_time >= timedelta(seconds=DOGON_DELAY):
                        current_signal.entry_time = datetime.utcnow()
                        await check_result()

            await asyncio.sleep(CHECK_INTERVAL)

        except Exception as e:
            logger.error(f"Ошибка в мониторинге: {e}")
            await asyncio.sleep(CHECK_INTERVAL)


# ================== ЗАПУСК ==================

if __name__ == "__main__":
    asyncio.run(monitor_levels())

