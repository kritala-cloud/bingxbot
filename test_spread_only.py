from core.bingx_futures_client import BingxFuturesClient
import time

client = BingxFuturesClient()

symbol = "AUTISM-USDT"

print("="*60)
print(f"ПРОВЕРКА РАЗНИЦЫ МЕЖДУ LAST И FAIR PRICE")
print(f"Монета: {symbol}")
print("="*60)

# Получаем fair price (mark price)
fair_price = client.get_mark_price(symbol)
if not fair_price:
    print("❌ Не удалось получить fair price")
    exit()

# Получаем last price (последняя сделка) из тикера
endpoint = "/openApi/swap/v2/quote/ticker"
params = {'symbol': symbol.upper()}
ticker_result = client._request('GET', endpoint, params)

last_price = None
if ticker_result and ticker_result.get('code') == 0 and ticker_result.get('data'):
    last_price = float(ticker_result['data'].get('lastPrice', 0))

if not last_price:
    print("❌ Не удалось получить last price")
    exit()

print(f"\n📈 Last price (последняя сделка): {last_price} USDT")
print(f"📊 Fair price (справедливая): {fair_price} USDT")

# Считаем разницу
diff = ((fair_price - last_price) / last_price) * 100
diff_abs = abs(diff)

print(f"\n📊 РАЗНИЦА: {diff_abs:.2f}%")

if fair_price > last_price:
    print(f"   Fair > Last на {diff_abs:.2f}% (бычий сигнал)")
elif fair_price < last_price:
    print(f"   Fair < Last на {diff_abs:.2f}% (медвежий сигнал)")
else:
    print("   Fair = Last (нет разницы)")

print("\n" + "-"*40)
print("ПРОВЕРКА УСЛОВИЙ:")
print(f"Для LONG: нужно Fair > Last")
print(f"Для SHORT: нужно Fair < Last")
print(f"Минимальная разница: 5%")

print("\n" + "="*60)
if diff_abs >= 5.0:
    print(f"✅ Разница {diff_abs:.2f}% >= 5% - можно открывать позицию")
else:
    print(f"❌ Разница {diff_abs:.2f}% < 5% - НЕЛЬЗЯ открывать позицию")
print("="*60)