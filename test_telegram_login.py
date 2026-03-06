import asyncio
from telethon import TelegramClient
import os
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
phone = os.getenv('TELEGRAM_PHONE')

print("=" * 50)
print("ПРОВЕРКА ПОДКЛЮЧЕНИЯ К TELEGRAM")
print("=" * 50)
print(f"API ID: {api_id} (тип: {type(api_id)})")
print(f"API Hash: {api_hash}")
print(f"Phone: {phone}")
print("=" * 50)

async def test_connection():
    # Создаем клиента
    client = TelegramClient('session/test_session', int(api_id), api_hash)
    
    try:
        print("🔄 Попытка подключения...")
        await client.start(phone=phone)
        
        me = await client.get_me()
        print(f"✅ УСПЕХ! Вошли как: {me.first_name} (@{me.username})")
        
        await client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print(f"Тип ошибки: {type(e)}")
        return False

# Запускаем тест
asyncio.run(test_connection())