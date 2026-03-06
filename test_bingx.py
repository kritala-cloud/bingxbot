import time
import requests
import hmac
from hashlib import sha256
import re

APIURL = "https://open-api.bingx.com"
APIKEY = "76JG4AzXlzBEiXTXX3mqDsxBJi64V4J53QFEEP0ZzKiqY2ep8jf8u18QdPPkX9Yq7Ungp7VlooTns92nag"
SECRETKEY = "6j45TfoTuStLboDJb0AKFqXgQdpHsSGyByDem8wdtvLW1nheGurcOmTBNg9bTXFO08I2QjIpzXY5e5oaBig"

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    return signature

def send_request(method, path, paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join([f"{k}={paramsMap[k]}" for k in sortedKeys])
    timestamp = str(int(time.time() * 1000))
    paramsStr = paramsStr + "&timestamp=" + timestamp
    signature = get_sign(SECRETKEY, paramsStr)
    url = f"{APIURL}{path}?{paramsStr}&signature={signature}"
    headers = {'X-BX-APIKEY': APIKEY}
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    else:
        response = requests.post(url, headers=headers)
    return response.json()

def open_position_with_min_qty(symbol, side, start_qty=2000):
    """Пытается открыть позицию, увеличивая количество до минимального"""
    qty = start_qty
    max_attempts = 10
    
    for attempt in range(max_attempts):
        print(f"\n🔄 Попытка {attempt + 1}: пробуем {qty} контрактов")
        
        order = send_request("POST", "/openApi/swap/v2/trade/order", {
            "symbol": symbol,
            "side": "SELL" if side == "SHORT" else "BUY",
            "positionSide": side,
            "type": "MARKET",
            "quantity": str(qty)
        })
        
        # Если успешно
        if order.get('code') == 0:
            print(f"✅ УСПЕХ! Позиция открыта с {qty} контрактов")
            return order
        
        # Если ошибка о минимальном количестве
        if order.get('code') == 101400 and 'minimum order amount' in order.get('msg', ''):
            # Вытаскиваем число из сообщения
            match = re.search(r'(\d+)', order['msg'])
            if match:
                min_qty = int(match.group(1))
                print(f"ℹ️ Минимальное количество: {min_qty}")
                qty = min_qty  # Устанавливаем точное минимальное
            else:
                qty += 100  # Если не смогли распарсить, увеличиваем на 100
        else:
            # Другая ошибка
            print(f"❌ Ошибка: {order}")
            return order
    
    print("❌ Не удалось открыть позицию после всех попыток")
    return None

# ТЕСТ 1: Баланс
print("=" * 50)
print("ТЕСТ БАЛАНСА")
print("=" * 50)
balance = send_request("GET", "/openApi/swap/v2/user/balance", {})
print("Баланс:", balance)

# ТЕСТ 2: Установка плеча
print("\n" + "=" * 50)
print("УСТАНОВКА ПЛЕЧА")
print("=" * 50)
leverage = send_request("POST", "/openApi/swap/v2/trade/leverage", {
    "symbol": "THEONEPIECE-USDT",
    "side": "SHORT",
    "leverage": "10"
})
print("Плечо установлено:", leverage)

# ТЕСТ 3: Открытие позиции с автоматическим подбором количества
print("\n" + "=" * 50)
print("ОТКРЫТИЕ ПОЗИЦИИ (АВТОПОДБОР)")
print("=" * 50)
result = open_position_with_min_qty("THEONEPIECE-USDT", "SHORT", start_qty=2000)
print("\n📊 Итоговый результат:", result)