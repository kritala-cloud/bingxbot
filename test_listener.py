import asyncio
import logging
from telethon import TelegramClient, events
from config.settings import Config

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("=" * 50)
    logger.info("ТЕСТОВЫЙ СЛУШАТЕЛЬ TELEGRAM")
    logger.info("=" * 50)
    
    # Данные из конфига
    api_id = int(Config.TELEGRAM_API_ID)
    api_hash = Config.TELEGRAM_API_HASH
    phone = Config.TELEGRAM_PHONE
    channel_id = Config.TELEGRAM_CHANNEL_ID
    
    logger.info(f"📱 Номер: {phone}")
    logger.info(f"🆔 API ID: {api_id}")
    logger.info(f"📢 Канал: {channel_id}")
    
    # Создаем клиента с другой сессией
    client = TelegramClient('session/test_listener', api_id, api_hash)
    
    try:
        # Запускаем
        await client.start(phone=phone)
        me = await client.get_me()
        logger.info(f"✅ Вошли как: {me.first_name}")
        
        # Получаем канал
        try:
            channel = await client.get_entity(channel_id)
            logger.info(f"✅ Нашли канал: {channel.title}")
        except Exception as e:
            logger.error(f"❌ Не могу найти канал: {e}")
            return
        
        # Пробуем разные способы получения сообщений
        
        # Способ 1: Получить последние сообщения
        logger.info("📨 Получаем последние 5 сообщений...")
        messages = await client.get_messages(channel, limit=5)
        for i, msg in enumerate(messages):
            if msg.message:
                logger.info(f"  [{i+1}] {msg.message[:100]}")
        
        # Способ 2: Регистрируем обработчик на ВСЕ новые сообщения (не только из канала)
        @client.on(events.NewMessage)
        async def handler_all(event):
            chat = await event.get_chat()
            logger.info(f"⚡ НОВОЕ СООБЩЕНИЕ В ЧАТЕ: {getattr(chat, 'title', 'личный чат')}")
            logger.info(f"📝 Текст: {event.message.text[:100]}")
        
        # Способ 3: Специфичный обработчик для канала
        @client.on(events.NewMessage(chats=channel))
        async def handler_channel(event):
            logger.info(f"🎯 НОВОЕ СООБЩЕНИЕ В КАНАЛЕ {channel.title}")
            logger.info(f"📝 Текст: {event.message.text[:100]}")
            
            # Отвечаем в канал
            try:
                await event.reply("✅ Бот получил сообщение!")
                logger.info("✅ Ответ отправлен")
            except:
                pass
        
        logger.info("👂 Слушаем все сообщения...")
        logger.info("⏳ Отправьте тестовое сообщение в канал")
        logger.info("🔴 Нажмите Ctrl+C для остановки")
        
        # Держим соединение
        await client.run_until_disconnected()
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())