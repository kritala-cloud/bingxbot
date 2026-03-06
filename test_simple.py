# test_simple.py
print("=" * 50)
print("ТЕСТИРОВАНИЕ ИМПОРТА")
print("=" * 50)

try:
    print("Попытка импорта из telegram.client...")
    from telegram.client import TelegramUserClient
    print("✅ ИМПОРТ УСПЕШЕН!")
    print(f"📦 Класс: {TelegramUserClient}")
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    
print("\nСодержимое папки telegram:")
import os
for file in os.listdir("telegram"):
    print(f"  📄 {file}")