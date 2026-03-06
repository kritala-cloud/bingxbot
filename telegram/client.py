import os
import logging
import asyncio
import time
from telethon import TelegramClient, events
from config.settings import Config
from core.bingx_futures_client import BingxFuturesClient

logger = logging.getLogger(__name__)

class TelegramUserClient:
    def __init__(self):
        self.api_id = int(Config.TELEGRAM_API_ID)
        self.api_hash = Config.TELEGRAM_API_HASH
        self.phone = Config.TELEGRAM_PHONE
        self.channel_id = Config.TELEGRAM_CHANNEL_ID
        self.notification_user = Config.TELEGRAM_NOTIFICATION_USER
        self.session_path = "session/user_session"
        self.client = None
        self.channel = None
        self.last_message_id = 0
        self.running = True
        self.bingx_client = None
        
    async def check_new_messages(self):
        """Периодическая проверка новых сообщений (каждую 1 секунду)"""
        logger.info("🔄 Запуск периодической проверки сообщений (каждую секунду)...")
        
        while self.running:
            try:
                if self.client and self.channel:
                    messages = await self.client.get_messages(self.channel, limit=10)
                    
                    for msg in reversed(messages):
                        if msg.id > self.last_message_id and msg.message:
                            logger.info(f"📨 НОВОЕ СООБЩЕНИЕ НАЙДЕНО! ID: {msg.id}")
                            logger.info(f"📝 Текст: {msg.message[:200]}")
                            
                            self.last_message_id = msg.id
                            
                            from telegram.handlers import handle_signal_message
                            
                            class SimpleEvent:
                                def __init__(self, msg, chat, client):
                                    self.message = msg
                                    self._chat = chat
                                    self.client = client
                                    
                                async def get_chat(self):
                                    return self._chat
                                    
                                async def reply(self, text):
                                    logger.info(f"📝 Сигнал обработан: {text[:50]}")
                                    return
                            
                            simple_event = SimpleEvent(msg, self.channel, self.client)
                            
                            try:
                                await handle_signal_message(simple_event)
                            except Exception as e:
                                logger.error(f"❌ Ошибка обработки сообщения {msg.id}: {e}")
                            
            except Exception as e:
                logger.error(f"❌ Ошибка при проверке сообщений: {e}")
            
            await asyncio.sleep(1)
    
    async def start(self):
        """Запуск Telegram клиента"""
        logger.info("🔄 Запуск Telegram клиента...")
        
        logger.info(f"📱 Номер телефона: {self.phone}")
        logger.info(f"🆔 API ID: {self.api_id}")
        
        os.makedirs("session", exist_ok=True)
        
        try:
            self.client = TelegramClient(self.session_path, self.api_id, self.api_hash)
            
            await self.client.start(phone=self.phone)
            
            me = await self.client.get_me()
            logger.info(f"✅ Успешный вход: {me.first_name}")
            
            try:
                self.channel = await self.client.get_entity(self.channel_id)
                logger.info(f"📢 Подключен к каналу: {self.channel.title}")
                logger.info(f"🆔 ID канала: {self.channel.id}")
                
                last_messages = await self.client.get_messages(self.channel, limit=1)
                if last_messages:
                    self.last_message_id = last_messages[0].id
                    logger.info(f"📨 Последнее сообщение ID: {self.last_message_id}")
                
                # СОЗДАЕМ КЛИЕНТА BINGX
                self.bingx_client = BingxFuturesClient()
                self.bingx_client.telegram_client = self.client
                
                # НАСТРАИВАЕМ ПОЛУЧАТЕЛЯ УВЕДОМЛЕНИЙ
                if self.notification_user:
                    try:
                        if self.notification_user.startswith('@'):
                            user_entity = await self.client.get_entity(self.notification_user)
                        else:
                            user_entity = await self.client.get_entity(int(self.notification_user))
                        
                        self.bingx_client.notification_user = user_entity.id
                        logger.info(f"📨 Уведомления будут отправляться пользователю: {self.notification_user}")
                    except Exception as e:
                        logger.error(f"❌ Не удалось найти пользователя {self.notification_user}: {e}")
                        self.bingx_client.notification_user = me.id
                        logger.info(f"📨 Уведомления будут отправляться вам (запасной вариант)")
                else:
                    self.bingx_client.notification_user = me.id
                    logger.info(f"📨 Уведомления будут отправляться вам (по умолчанию)")
                
                try:
                    start_message = (
                        f"🤖 **БОТ ЗАПУЩЕН**\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"📱 Аккаунт: {me.first_name}\n"
                        f"📢 Канал: {self.channel.title}\n"
                        f"💵 Маржа: {Config.TRADE_AMOUNT_USDT} USDT\n"
                        f"📊 Проверка канала: каждую секунду\n"
                        f"📊 Мониторинг позиций: каждую секунду\n"
                        f"🕐 Время запуска: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"✅ Бот готов к работе!"
                    )
                    
                    await self.client.send_message(self.bingx_client.notification_user, start_message)
                    logger.info(f"📨 Отправлено уведомление о запуске")
                except Exception as e:
                    logger.error(f"❌ Не удалось отправить уведомление о запуске: {e}")
                
                logger.info("✅ BingX клиент инициализирован и связан с Telegram")
                
                asyncio.create_task(self.check_new_messages())
                
                logger.info("👂 Начинаем прослушивание канала (проверка каждую секунду)...")
                
            except Exception as e:
                logger.error(f"❌ Ошибка подключения к каналу: {e}")
                return
            
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске: {e}")
            raise
    
    async def stop(self):
        """Остановка клиента"""
        self.running = False
        if self.client:
            await self.client.disconnect()
            logger.info("🔌 Клиент отключен")