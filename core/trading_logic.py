import logging
from core.bingx_futures_client import BingxFuturesClient
from config.settings import Config

logger = logging.getLogger(__name__)
client = BingxFuturesClient()

def execute_trade(symbol, side):
    """
    Выполнить сделку с параметрами ИЗ .env
    """
    logger.info("=" * 60)
    logger.info("🚀 ТОРГОВЛЯ НА BINGX")
    logger.info("=" * 60)
    logger.info(f"💰 Символ: {symbol}")
    logger.info(f"📈 Сторона: {side}")
    logger.info(f"⚙️ LEVERAGE = {Config.LEVERAGE}x (из .env)")
    logger.info(f"💵 TRADE_AMOUNT_USDT = {Config.TRADE_AMOUNT_USDT} USDT (из .env)")
    logger.info("=" * 60)
    
    try:
        # Проверяем баланс
        balance = client.get_balance()
        if balance and balance.get('code') == 0:
            available = float(balance['data']['balance']['availableMargin'])
            logger.info(f"💰 Доступно: {available} USDT")
        
        # Открываем позицию
        result = client.open_position(symbol, side)
        
        if result and result.get('code') == 0:
            logger.info("✅ СДЕЛКА ВЫПОЛНЕНА!")
            return result
        else:
            logger.error("❌ Ошибка")
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return None