import asyncio
import logging
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация (вставьте свои данные)
API_ID = 30026073
API_HASH = "c3dc14e865f64dc19ab6084955fc4d8d"
PHONE = "+14473442796"
CHANNEL = "@kritala1488"  # или https://t.me/b

async def main():
    logger.info("=" * 50)
    logger.info("УЛУЧШЕННЫЙ ТЕСТОВЫЙ СЛУШАТЕЛЬ")
    logger.info("=" * 50)
    
    # Создаем клиента
    client = TelegramClient('session/fixed_test', API_ID, API_HASH)
    
    try:
        # Запускаем
        await client.start(phone=PHONE)
        me = await client.get_me()
        logger.info(f"✅ Вошли как: {me.first_name}")
        
        # Получаем канал
        try:
            channel = await client.get_entity(CHANNEL)
            logger.info(f"✅ Нашли канал: {channel.title}")
            logger.info(f"✅ ID канала: {channel.id}")
        except Exception as e:
            logger.error(f"❌ Не могу найти канал: {e}")
            return
        
        # Получаем последние сообщения для проверки
        logger.info("📨 Последние 5 сообщений:")
        messages = await client.get_messages(channel, limit=5)
        for i, msg in enumerate(messages):
            if msg.message:
                logger.info(f"  [{i+1}] {msg.message[:100]}")
        
        # СПОСОБ 1: Обработчик на все новые сообщения
        @client.on(events.NewMessage)
        async def handler_all(event):
            try:
                chat = await event.get_chat()
                chat_title = getattr(chat, 'title', 'личный чат')
                logger.info(f"📢 ВСЕ: Новое сообщение в чате '{chat_title}'")
                
                # Проверяем, это наш канал?
                if hasattr(chat, 'id') and chat.id == channel.id:
                    logger.info(f"🎯 ЭТО НАШ КАНАЛ! Сообщение: {event.message.text[:100]}")
                    await event.reply("✅ Бот получил сообщение!")
            except Exception as e:
                logger.error(f"Ошибка в обработчике: {e}")
        
        # СПОСОБ 2: Специфичный обработчик
        @client.on(events.NewMessage(chats=channel))
        async def handler_specific(event):
            logger.info(f"🎯 СПЕЦИФИЧНЫЙ: Сообщение в канале: {event.message.text[:100]}")
            await event.reply("✅ Получил сигнал!")
        
        # СПОСОБ 3: Периодическая проверка новых сообщений
        async def periodic_check():
            last_id = 0
            while True:
                try:
                    # Получаем последние сообщения
                    messages = await client.get_messages(channel, limit=1)
                    if messages and messages[0].id > last_id:
                        last_id = messages[0].id
                        logger.info(f"🔄 ПЕРИОДИЧЕСКАЯ: Новое сообщение: {messages[0].message[:100]}")
                except Exception as e:
                    logger.error(f"Ошибка при периодической проверке: {e}")
                
                await asyncio.sleep(5)  # Проверяем каждые 5 секунд
        
        # Запускаем периодическую проверку в фоне
        asyncio.create_task(periodic_check())
        
        logger.info("👂 Слушаем всеми способами...")
        logger.info("📝 Отправьте сообщение в канал:")
        logger.info("   🟢 $BTC  или  🔴 $ETH")
        logger.info("")
        logger.info("🔴 Нажмите Ctrl+C для остановки")
        
        # Держим соединение
        await client.run_until_disconnected()
        
    except FloodWaitError as e:
        logger.error(f"❌ Flood wait: нужно подождать {e.seconds} секунд")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Программа остановлена")