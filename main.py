import asyncio
import logging
import sys
from pathlib import Path

# Добавляем текущую папку в путь поиска модулей
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config.settings import Config
    from telegram.client import TelegramUserClient
    from utils.logger import setup_logger
    print("✅ Все модули импортированы успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Текущая директория:", Path.cwd())
    print("Файлы в папке:", list(Path.cwd().glob('*')))
    sys.exit(1)

async def main():
    # Настройка логирования
    setup_logger()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("🚀 Запуск BingX Trading Bot")
    logger.info("=" * 50)
    
    # Проверка конфигурации
    errors = Config.validate()
    if errors:
        logger.error("❌ Ошибки конфигурации:")
        for error in errors:
            logger.error(f"   - {error}")
        logger.error("📝 Проверьте файл .env")
        return
    
    logger.info("✅ Конфигурация загружена")
    
    # Создаем и запускаем Telegram клиент
    telegram_client = TelegramUserClient()
    
    try:
        await telegram_client.start()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await telegram_client.stop()
        logger.info("👋 Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())