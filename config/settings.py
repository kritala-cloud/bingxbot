import os
from dotenv import load_dotenv
from pathlib import Path

# Загружаем .env файл
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Config:
    # BingX API
    BINGX_API_KEY = os.getenv('BINGX_API_KEY')
    BINGX_SECRET_KEY = os.getenv('BINGX_SECRET_KEY')
    
    # Фьючерсные настройки
    LEVERAGE = int(os.getenv('LEVERAGE', '10'))
    MARGIN_MODE = os.getenv('MARGIN_MODE', 'ISOLATED')
    TRADE_AMOUNT_USDT = float(os.getenv('TRADE_AMOUNT_USDT', '10'))
    POSITION_SIDE = os.getenv('POSITION_SIDE', 'BOTH')
    
    # Telegram Client
    TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
    TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
    TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
    TELEGRAM_NOTIFICATION_USER = os.getenv('TELEGRAM_NOTIFICATION_USER')  # ДОБАВЛЕНО
    
    @classmethod
    def validate(cls):
        """Проверка наличия всех необходимых переменных"""
        errors = []
        
        # Проверка BingX
        if not cls.BINGX_API_KEY:
            errors.append("BINGX_API_KEY не установлен")
        if not cls.BINGX_SECRET_KEY:
            errors.append("BINGX_SECRET_KEY не установлен")
        
        # Проверка Telegram
        if not cls.TELEGRAM_API_ID:
            errors.append("TELEGRAM_API_ID не установлен")
        if not cls.TELEGRAM_API_HASH:
            errors.append("TELEGRAM_API_HASH не установлен")
        if not cls.TELEGRAM_PHONE:
            errors.append("TELEGRAM_PHONE не установлен")
        if not cls.TELEGRAM_CHANNEL_ID:
            errors.append("TELEGRAM_CHANNEL_ID не установлен")
            
        return errors