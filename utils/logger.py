import logging
import sys
from pathlib import Path

def setup_logger():
    """Настройка логирования"""
    
    # Создаем форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Очищаем существующие обработчики
    root_logger.handlers.clear()
    
    # Создаем обработчик для файла
    file_handler = logging.FileHandler(
        Path(__file__).parent.parent / 'trading_bot.log',
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Создаем обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Подавляем лишние логи от telethon
    logging.getLogger('telethon').setLevel(logging.WARNING)
    
    # Логируем запуск
    logger = logging.getLogger(__name__)
    logger.info("✅ Логирование настроено")
    
    return root_logger

# Для обратной совместимости
def get_logger(name=None):
    """Получить логгер с указанным именем"""
    return logging.getLogger(name)

print("✅ Модуль utils.logger загружен")
print("📦 Функция setup_logger создана")