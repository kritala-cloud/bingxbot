import requests
import time
import hashlib
import hmac
import threading
import logging
import re
from urllib.parse import urlencode

from config.settings import Config

logger = logging.getLogger(__name__)

class BingxFuturesClient:
    def __init__(self):
        self.api_key = Config.BINGX_API_KEY
        self.secret_key = Config.BINGX_SECRET_KEY
        self.base_url = "https://open-api.bingx.com"
        self.active_positions = {}
        self.telegram_client = None
        self.notification_user = None
        self.check_and_close_positions()
        
    def _generate_signature(self, params):
        """Генерация подписи для запроса"""
        sorted_params = dict(sorted(params.items()))
        query_string = '&'.join([f"{k}={v}" for k, v in sorted_params.items()])
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(self, method, endpoint, params=None):
        """Базовый метод для отправки запросов"""
        if params is None:
            params = {}
        
        params['timestamp'] = int(time.time() * 1000)
        
        sorted_params = dict(sorted(params.items()))
        query_string = '&'.join([f"{k}={v}" for k, v in sorted_params.items()])
        signature = self._generate_signature(params)
        url = f"{self.base_url}{endpoint}?{query_string}&signature={signature}"
        
        headers = {'X-BX-APIKEY': self.api_key}
        
        logger.info(f"🔐 {method} {endpoint}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            else:
                response = requests.post(url, headers=headers)
            
            result = response.json()
            logger.info(f"📨 Ответ: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Ошибка запроса: {e}")
            return None
    
    def get_balance(self):
        """Получить баланс USDT"""
        endpoint = "/openApi/swap/v2/user/balance"
        return self._request('GET', endpoint, {})
    
    def get_contract_info(self, symbol):
        """
        Получить информацию о контракте
        Возвращает: минимальное количество, максимальное плечо и т.д.
        """
        endpoint = "/openApi/swap/v2/quote/contracts"
        params = {'symbol': symbol.upper()}
        result = self._request('GET', endpoint, params)
        
        if result and result.get('code') == 0 and result.get('data'):
            contract_data = result['data'][0]
            logger.info(f"📄 Данные контракта {symbol}: {contract_data}")
            return contract_data
        return None
    
    def get_max_leverage(self, symbol):
        """
        Получить МАКСИМАЛЬНОЕ ПЛЕЧО для символа ИЗ API
        У каждой монеты свое!
        """
        try:
            contract_data = self.get_contract_info(symbol)
            if contract_data:
                if 'maxLeverage' in contract_data:
                    max_lev = int(contract_data['maxLeverage'])
                    logger.info(f"📊 Макс. плечо для {symbol}: {max_lev}x (из maxLeverage)")
                    return max_lev
                elif 'leverage' in contract_data:
                    max_lev = int(contract_data['leverage'])
                    logger.info(f"📊 Макс. плечо для {symbol}: {max_lev}x (из leverage)")
                    return max_lev
            
            endpoint = "/openApi/swap/v2/trade/leverage"
            params = {'symbol': symbol.upper()}
            result = self._request('GET', endpoint, params)
            
            if result and result.get('code') == 0 and result.get('data'):
                data = result['data']
                if 'maxLeverage' in data:
                    max_lev = int(data['maxLeverage'])
                    logger.info(f"📊 Макс. плечо для {symbol}: {max_lev}x (из trade/leverage)")
                    return max_lev
                    
        except Exception as e:
            logger.error(f"❌ Ошибка получения макс. плеча для {symbol}: {e}")
        
        logger.warning(f"⚠️ Не удалось получить макс. плечо для {symbol}, ставлю 20x")
        return 20
    
    def get_min_quantity(self, symbol):
        """Получить минимальное количество контрактов для символа"""
        try:
            contract_data = self.get_contract_info(symbol)
            if contract_data and 'tradeMinQuantity' in contract_data:
                min_qty = int(contract_data['tradeMinQuantity'])
                logger.info(f"📊 Минимальное количество для {symbol}: {min_qty}")
                return min_qty
        except Exception as e:
            logger.error(f"❌ Ошибка получения мин. количества: {e}")
        return 1
    
    def get_max_position_value(self, symbol):
        """
        Получить максимальный объем позиции для монетки
        """
        try:
            contract_data = self.get_contract_info(symbol)
            if contract_data:
                if 'maxPositionValue' in contract_data:
                    return float(contract_data['maxPositionValue'])
                elif 'maxQty' in contract_data:
                    price = self.get_mark_price(symbol)
                    if price:
                        return float(contract_data['maxQty']) * price
        except Exception as e:
            logger.error(f"❌ Ошибка получения макс. объема: {e}")
        return None
    
    def get_mark_price(self, symbol):
        """Получить текущую цену для расчета количества контрактов"""
        endpoint = "/openApi/swap/v2/quote/premiumIndex"
        params = {'symbol': symbol.upper()}
        result = self._request('GET', endpoint, params)
        
        if result and result.get('code') == 0 and result.get('data'):
            price = float(result['data'].get('markPrice', 0))
            logger.info(f"💰 Текущая цена {symbol}: {price} USDT")
            return price
        return None
    
    def set_leverage(self, symbol, leverage):
        """Установить плечо для символа"""
        endpoint = "/openApi/swap/v2/trade/leverage"
        params = {
            'symbol': symbol.upper(),
            'leverage': str(leverage)
        }
        return self._request('POST', endpoint, params)
    
    def get_orderbook(self, symbol, limit=20):
        """Получить стакан заявок (order book)"""
        endpoint = "/openApi/swap/v2/quote/depth"
        params = {
            'symbol': symbol.upper(),
            'limit': limit
        }
        result = self._request('GET', endpoint, params)
        
        if result and result.get('code') == 0 and result.get('data'):
            data = result['data']
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            logger.info(f"📊 Стакан: {len(bids)} bids, {len(asks)} asks")
            return {'bids': bids, 'asks': asks}
        return None
    
    def get_positions(self, symbol=None):
        """Получить открытые позиции (исправлено)"""
        endpoint = "/openApi/swap/v2/trade/positionRisk"  # Правильный эндпоинт
        params = {}
        if symbol:
            params['symbol'] = symbol.upper()
        return self._request('GET', endpoint, params)
    
    async def send_telegram_notification(self, message):
        """Отправить уведомление в Telegram указанному пользователю"""
        if self.telegram_client and self.notification_user:
            try:
                await self.telegram_client.send_message(self.notification_user, message)
                logger.info(f"📨 Уведомление отправлено пользователю {self.notification_user}")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки уведомления: {e}")
    
    def check_and_close_positions(self):
        """
        Мониторинг позиций КАЖДУЮ СЕКУНДУ
        Если спред < 2% держится 10 секунд подряд - закрывает
        """
        def check_loop():
            low_spread_counter = {}
            
            while True:
                try:
                    if not self.active_positions:
                        time.sleep(1)
                        continue
                    
                    logger.info("=" * 60)
                    logger.info("🔍 ПРОВЕРКА ОТКРЫТЫХ ПОЗИЦИЙ (каждую секунду)")
                    logger.info("=" * 60)
                    
                    positions_to_check = list(self.active_positions.items())
                    
                    for symbol, pos_info in positions_to_check:
                        logger.info(f"\n📊 Проверка {symbol} {pos_info['side']}")
                        
                        fair_price = self.get_mark_price(symbol)
                        if not fair_price:
                            continue
                        
                        endpoint = "/openApi/swap/v2/quote/ticker"
                        params = {'symbol': symbol.upper()}
                        ticker_result = self._request('GET', endpoint, params)
                        
                        last_price = None
                        if ticker_result and ticker_result.get('code') == 0 and ticker_result.get('data'):
                            last_price = float(ticker_result['data'].get('lastPrice', 0))
                        
                        if not last_price:
                            continue
                        
                        diff = ((fair_price - last_price) / last_price) * 100
                        diff_abs = abs(diff)
                        
                        logger.info(f"   📈 Last: {last_price}")
                        logger.info(f"   📊 Fair: {fair_price}")
                        logger.info(f"   📊 Разница: {diff_abs:.2f}%")
                        
                        # Проверяем условие для закрытия (спред < 2%)
                        if diff_abs < 2.0:
                            if symbol not in low_spread_counter:
                                low_spread_counter[symbol] = 1
                                logger.info(f"   ⚠️ Секунда 1: разница {diff_abs:.2f}% < 2%")
                            else:
                                low_spread_counter[symbol] += 1
                                logger.info(f"   ⚠️ Секунда {low_spread_counter[symbol]}: разница {diff_abs:.2f}% < 2%")
                            
                            # Если 10 секунд подряд - закрываем
                            if low_spread_counter[symbol] >= 5:
                                logger.info(f"   🎯 10 секунд подряд спред < 2% - ЗАКРЫВАЮ ПОЗИЦИЮ")
                                
                                # Проверяем, существует ли еще позиция через правильный эндпоинт
                                positions_check = self._request('GET', '/openApi/swap/v2/trade/positionRisk', {'symbol': symbol.upper()})
                                position_exists = False
                                
                                if positions_check and positions_check.get('code') == 0:
                                    if 'data' in positions_check and isinstance(positions_check['data'], list):
                                        for pos in positions_check['data']:
                                            if pos.get('positionSide') == pos_info['side'].upper() and float(pos.get('positionAmt', 0)) != 0:
                                                position_exists = True
                                                break
                                
                                if position_exists:
                                    self.close_position(symbol, pos_info['side'])
                                    if symbol in low_spread_counter:
                                        del low_spread_counter[symbol]
                                else:
                                    logger.info(f"   ❌ Позиция уже не существует - удаляю")
                                    del self.active_positions[symbol]
                                    if symbol in low_spread_counter:
                                        del low_spread_counter[symbol]
                        else:
                            # Если спред стал нормальным - сбрасываем счетчик
                            if symbol in low_spread_counter:
                                logger.info(f"   ✅ Спред вернулся к норме ({diff_abs:.2f}% >= 2%), счетчик сброшен")
                                del low_spread_counter[symbol]
                            else:
                                logger.info(f"   ✅ Спред {diff_abs:.2f}% >= 2% - держим")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка в check_loop: {e}")
                    time.sleep(1)
        
        checker_thread = threading.Thread(target=check_loop, daemon=True)
        checker_thread.start()
        logger.info("✅ Запущен мониторинг позиций (каждую секунду, закрытие при 10 секундах спред <2%)")
    
    def close_position(self, symbol, side):
        """Закрыть позицию (исправлено)"""
        logger.info(f"🔴 ЗАКРЫТИЕ ПОЗИЦИИ {symbol} {side}")
        
        # Используем правильный эндпоинт для получения позиций
        positions = self._request('GET', '/openApi/swap/v2/trade/positionRisk', {'symbol': symbol.upper()})
        
        if not positions or positions.get('code') != 0:
            logger.error("❌ Не удалось получить информацию о позиции")
            return None
        
        quantity = 0
        
        if 'data' in positions and isinstance(positions['data'], list):
            for pos in positions['data']:
                if pos.get('positionSide') == side.upper():
                    quantity = float(pos.get('positionAmt', 0))
                    break
        
        if quantity <= 0:
            logger.error(f"❌ Не удалось найти позицию {side} для {symbol}")
            return None
        
        logger.info(f"📊 Количество контрактов в позиции: {quantity}")
        
        close_side = 'SELL' if side.upper() == 'LONG' else 'BUY'
        
        params = {
            'symbol': symbol.upper(),
            'side': close_side,
            'positionSide': side.upper(),
            'type': 'MARKET',
            'quantity': str(int(quantity)),
            'reduceOnly': 'true'
        }
        
        result = self._request('POST', '/openApi/swap/v2/trade/order', params)
        
        if result and result.get('code') == 0:
            logger.info(f"✅ Позиция {symbol} {side} закрыта")
            
            # Данные для уведомления
            pos_data = self.active_positions.get(symbol, {})
            open_time = pos_data.get('open_time', 'неизвестно')
            open_price = pos_data.get('price', 0)
            qty = pos_data.get('quantity', 0)
            
            current_price = self.get_mark_price(symbol)
            profit_loss = 0
            profit_percent = 0
            if current_price and open_price:
                if side.upper() == 'LONG':
                    profit_loss = (current_price - open_price) * qty
                    profit_percent = ((current_price - open_price) / open_price) * 100
                else:
                    profit_loss = (open_price - current_price) * qty
                    profit_percent = ((open_price - current_price) / open_price) * 100
            
            if symbol in self.active_positions:
                del self.active_positions[symbol]
            
            if self.telegram_client:
                import asyncio
                profit_emoji = "🟢" if profit_loss >= 0 else "🔴"
                notif_msg = (
                    f"🔴 **ПОЗИЦИЯ ЗАКРЫТА**\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"💰 Монета: {symbol}\n"
                    f"📉 Направление: {side}\n"
                    f"📊 Контрактов: {qty:,.0f}\n"
                    f"💵 Цена входа: ${open_price:.6f}\n"
                    f"💵 Цена выхода: ${current_price:.6f}\n"
                    f"{profit_emoji} P&L: ${profit_loss:.2f} ({profit_percent:.2f}%)\n"
                    f"🕐 Открыто: {open_time}\n"
                    f"🕐 Закрыто: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"━━━━━━━━━━━━━━━━"
                )
                asyncio.create_task(self.send_telegram_notification(notif_msg))
            
        else:
            logger.error(f"❌ Ошибка закрытия позиции: {result}")
        
        return result
    
    def open_position(self, symbol, side):
        """
        ОТКРЫТЬ ПОЗИЦИЮ С ПРОВЕРКОЙ РАЗНИЦЫ МЕЖДУ LAST И FAIR
        """
        margin = Config.TRADE_AMOUNT_USDT
        logger.info("=" * 60)
        logger.info("🚀 ОТКРЫТИЕ ПОЗИЦИИ")
        logger.info("=" * 60)
        logger.info(f"💰 Маржа из .env: {margin} USDT")
        
        max_leverage = self.get_max_leverage(symbol)
        logger.info(f"📊 Макс. плечо для {symbol}: {max_leverage}x")
        
        calculated_volume = margin * max_leverage
        logger.info(f"📊 Рассчитанный объем: {calculated_volume} USDT")
        
        logger.info("=" * 60)
        logger.info("📊 ПРОВЕРКА РАЗНИЦЫ LAST/FAIR")
        logger.info("=" * 60)
        
        fair_price = self.get_mark_price(symbol)
        if not fair_price:
            logger.error("❌ Не удалось получить fair price")
            return None
        
        endpoint = "/openApi/swap/v2/quote/ticker"
        params = {'symbol': symbol.upper()}
        ticker_result = self._request('GET', endpoint, params)
        
        last_price = None
        if ticker_result and ticker_result.get('code') == 0 and ticker_result.get('data'):
            last_price = float(ticker_result['data'].get('lastPrice', 0))
        
        if not last_price:
            logger.error("❌ Не удалось получить last price")
            return None
        
        logger.info(f"📈 Last: {last_price} USDT")
        logger.info(f"📊 Fair: {fair_price} USDT")
        
        diff = ((fair_price - last_price) / last_price) * 100
        diff_abs = abs(diff)
        
        logger.info(f"📊 Разница: {diff_abs:.2f}%")
        
        if side.upper() == 'LONG':
            direction_ok = fair_price > last_price
            logger.info(f"📈 Направление LONG: Fair > Last? {direction_ok}")
        else:
            direction_ok = fair_price < last_price
            logger.info(f"📉 Направление SHORT: Fair < Last? {direction_ok}")
        
        diff_ok = diff_abs >= 5.0
        logger.info(f"📊 Разница >= 5%? {diff_ok}")
        
        if not direction_ok or not diff_ok:
            logger.error("❌ Условия не выполнены - позиция НЕ открывается")
            return None
        
        logger.info("✅ Условия выполнены - открываем позицию")
        
        quantity = int(calculated_volume / fair_price)
        logger.info(f"🔢 Начальное количество: {quantity}")
        
        min_qty = self.get_min_quantity(symbol)
        if quantity < min_qty:
            quantity = min_qty
            logger.info(f"📊 Увеличиваем до минимального: {quantity}")
        
        logger.info(f"⚙️ Устанавливаю плечо {max_leverage}x")
        self.set_leverage(symbol, max_leverage)
        
        logger.info(f"🔄 Открываю позицию на {quantity} контрактов...")
        
        params = {
            'symbol': symbol.upper(),
            'side': 'SELL' if side.upper() == 'SHORT' else 'BUY',
            'type': 'MARKET',
            'quantity': str(quantity)
        }
        
        result = self._request('POST', '/openApi/swap/v2/trade/order', params)
        
        if result and result.get('code') == 101209:
            match = re.search(r'(\d+)', result['msg'])
            if match:
                max_volume = int(match.group(1))
                new_quantity = int(max_volume / fair_price)
                params['quantity'] = str(new_quantity)
                result = self._request('POST', '/openApi/swap/v2/trade/order', params)
        
        if result and result.get('code') == 101400 and 'minimum order amount' in result.get('msg', ''):
            match = re.search(r'(\d+)', result['msg'])
            if match:
                params['quantity'] = match.group(1)
                result = self._request('POST', '/openApi/swap/v2/trade/order', params)
        
        if result and result.get('code') == 0:
            order_data = result.get('data', {}).get('order', {})
            qty = float(order_data.get('quantity', 0))
            avg_price = float(order_data.get('avgPrice', 0))
            
            logger.info("=" * 60)
            logger.info("✅ ПОЗИЦИЯ ОТКРЫТА!")
            logger.info("=" * 60)
            logger.info(f"🆔 Order ID: {order_data.get('orderId')}")
            logger.info(f"📊 Контрактов: {qty}")
            logger.info(f"💵 Цена: {avg_price}")
            
            self.active_positions[symbol] = {
                "side": side,
                "order_id": order_data.get('orderId'),
                "quantity": qty,
                "price": avg_price,
                "open_time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if self.telegram_client:
                import asyncio
                notif_msg = (
                    f"🚀 **ПОЗИЦИЯ ОТКРЫТА**\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"💰 Монета: {symbol}\n"
                    f"📈 Направление: {side}\n"
                    f"📊 Контрактов: {qty:,.0f}\n"
                    f"💵 Цена входа: ${avg_price:.6f}\n"
                    f"💳 Маржа: {margin} USDT\n"
                    f"⚙️ Плечо: {max_leverage}x\n"
                    f"🕐 Время: {self.active_positions[symbol]['open_time']}\n"
                    f"━━━━━━━━━━━━━━━━"
                )
                asyncio.create_task(self.send_telegram_notification(notif_msg))
            
        else:
            logger.error(f"❌ Ошибка: {result}")
        
        return result