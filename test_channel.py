import asyncio
from telethon import TelegramClient
from config.settings import Config

async def test_channel():
    client = TelegramClient('session/test', int(Config.TELEGRAM_API_ID), Config.TELEGRAM_API_HASH)
    
    try:
        await client.start(phone=Config.TELEGRAM_PHONE)
        print("✅ Подключились к Telegram")
        
        # Пробуем получить канал
        channel = await client.get_entity(Config.TELEGRAM_CHANNEL_ID)
        print(f"✅ Нашли канал: {channel.title}")
        
        # Пробуем получить сообщения
        messages = await client.get_messages(channel, limit=3)
        print(f"📨 Последние сообщения:")
        for msg in messages:
            if msg.message:
                print(f"  - {msg.message[:100]}")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

asyncio.run(test_channel())