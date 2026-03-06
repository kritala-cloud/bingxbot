import re
import logging
from core.trading_logic import execute_trade
from config.settings import Config

logger = logging.getLogger(__name__)

async def handle_signal_message(event):
    """Обработка сигнальных сообщений из Telegram канала"""
    message = event.message.message
    chat = await event.get_chat()
    
    logger.info(f"📨 Получено сообщение из канала {chat.title}")
    logger.info(f"📝 Текст сообщения: {message[:100]}...")
    
    # Разбиваем сообщение на строки
    lines = message.strip().split('\n')
    if not lines:
        logger.warning("❌ Пустое сообщение")
        return
    
    # Первая строка содержит сигнал и тикер (например "🟢 $BARD")
    first_line = lines[0].strip()
    logger.info(f"🔍 Первая строка: {first_line}")
    
    # Определяем тип сигнала по первому символу
    signal_type = None
    if first_line.startswith('🟢'):
        signal_type = 'LONG'
        logger.info("✅ Сигнал LONG")
    elif first_line.startswith('🔴'):
        signal_type = 'SHORT'
        logger.info("✅ Сигнал SHORT")
    else:
        logger.info("⏭️ Не сигнал (нет 🟢 или 🔴), пропускаем")
        return
    
    # Ищем тикер в формате $BARD
    # Разбиваем первую строку на части
    parts = first_line.split()
    symbol = None
    
    for part in parts:
        # Ищем часть, начинающуюся с $
        if part.startswith('$'):
            # Убираем $ и возможные спецсимволы в конце
            raw_symbol = part[1:].strip()
            # Оставляем только буквы и цифры (убираем знаки препинания)
            symbol = re.sub(r'[^a-zA-Z0-9]', '', raw_symbol)
            logger.info(f"💰 Найден тикер из канала: {symbol}")
            break
    
    # Если не нашли с $, ищем просто слово после смайлика
    if not symbol and len(parts) >= 2:
        potential_symbol = parts[1].strip()
        symbol = re.sub(r'[^a-zA-Z0-9]', '', potential_symbol)
        logger.info(f"💰 Найден тикер (альтернативный метод): {symbol}")
    
    if not symbol:
        logger.warning("❌ Не удалось найти тикер в сообщении")
        logger.warning(f"   Первая строка: {first_line}")
        logger.warning(f"   Части: {parts}")
        return
    
    # Форматируем для BingX (добавляем -USDT)
    trading_symbol = f"{symbol}-USDT"
    logger.info(f"📊 Торговый символ для BingX: {trading_symbol}")
    
    # Выводим параметры сделки
    logger.info("=" * 50)
    logger.info("📊 ПАРАМЕТРЫ СДЕЛКИ")
    logger.info("=" * 50)
    logger.info(f"💰 Тикер из канала: {symbol}")
    logger.info(f"📈 Сигнал: {signal_type}")
    logger.info(f"📊 Торговый символ: {trading_symbol}")
    logger.info(f"⚙️ Плечо: {Config.LEVERAGE}x")
    logger.info(f"💵 Сумма: {Config.TRADE_AMOUNT_USDT} USDT")
    logger.info("=" * 50)
    
    # ВЫПОЛНЯЕМ СДЕЛКУ
    logger.info(f"🚀 ВЫПОЛНЯЮ СДЕЛКУ НА BINGX...")
    result = execute_trade(trading_symbol, signal_type)
    
    if result and result.get('code') == 0:
        logger.info(f"✅ СДЕЛКА ВЫПОЛНЕНА УСПЕШНО!")
    else:
        logger.error(f"❌ СДЕЛКА НЕ ВЫПОЛНЕНА")