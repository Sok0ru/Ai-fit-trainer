#!/usr/bin/env python3
"""
Тестирование OpenAI через ProxyAPI (официальный SDK)
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_proxy_openai():
    print("=" * 70)
    print("ТЕСТИРОВАНИЕ OPENAI ЧЕРЕЗ PROXYAPI (официальный SDK)")
    print("=" * 70)
    
    # Проверка переменных
    api_key = os.getenv('PROXY_API_KEY')
    if not api_key:
        print("❌ PROXY_API_KEY не установлен")
        print("   Получите ключ на https://proxyapi.ru")
        return False
    
    print(f"✅ PROXY_API_KEY: {api_key[:20]}...")
    
    model = os.getenv('PROXY_MODEL', 'openai/gpt-5-nano')
    print(f"✅ Модель: {model}")
    
    base_url = os.getenv('PROXY_API_URL', 'https://openai.api.proxyapi.ru/v1')
    print(f"✅ Base URL: {base_url}")
    
    # Проверка импорта
    try:
        from proxy_openai_integration import ProxyOpenAI
        print("✅ Модуль ProxyOpenAI загружен")
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    
    # Тестирование
    try:
        print(f"\n🧪 Инициализация OpenAI клиента через ProxyAPI...")
        proxy = ProxyOpenAI()
        
        print("🧪 Тест подключения...")
        if proxy.test_connection():
            print("✅ Подключение к ProxyAPI успешно")
            
            # Тест генерации плана
            print("\n🧪 Тест генерации фитнес-плана...")
            test_data = {
                'name': 'Алексей Иванов',
                'age': 32,
                'height': 178,
                'weight': 82,
                'fitness_level': 'Средний',
                'goals': 'Похудеть на 7 кг, укрепить мышцы спины и пресс',
                'injuries': 'Периодические боли в пояснице',
                'preferences': 'Функциональный тренинг, плавание',
                'equipment': 'Домашние гантели, коврик, резиновые ленты'
            }
            
            plan = proxy.generate_plan(test_data)
            if plan:
                print(f"✅ План успешно сгенерирован!")
                print(f"📏 Длина: {len(plan)} символов")
                print("\n📝 Превью плана:")
                print("=" * 60)
                print(plan[:500] + "..." if len(plan) > 500 else plan)
                print("=" * 60)
                
                # Расчет стоимости
                print("\n💰 РАСЧЕТ СТОИМОСТИ:")
                print(f"Модель: {model}")
                print("Примерная стоимость одного плана: 0.15 - 0.20 ₽")
                print("При 100 пользователях в месяц: 15 - 20 ₽")
                print("При 1000 пользователях: 150 - 200 ₽")
                
                return True
            else:
                print("❌ Не удалось сгенерировать план")
                return False
        else:
            print("❌ Не удалось подключиться к ProxyAPI")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_proxy_openai()
    print("\n" + "=" * 70)
    print(f"РЕЗУЛЬТАТ: {'✅ УСПЕХ' if success else '❌ ПРОВАЛ'}")
    print("=" * 70)
    sys.exit(0 if success else 1)
