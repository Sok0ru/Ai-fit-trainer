#!/usr/bin/env python3
import sys
import os
import logging

# Добавляем путь для импорта
sys.path.append('/app')

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_diagnostics():
    print("=" * 60)
    print("Диагностика подключения к GigaChat API")
    print("=" * 60)
    
    # Проверка переменных окружения
    print("\n1. Проверка переменных окружения:")
    print(f"   GIGACHAT_API_KEY: {'Установлен' if os.getenv('GIGACHAT_API_KEY') else 'НЕ УСТАНОВЛЕН'}")
    print(f"   GIGACHAT_AUTH_URL: {os.getenv('GIGACHAT_AUTH_URL')}")
    print(f"   GIGACHAT_API_URL: {os.getenv('GIGACHAT_API_URL')}")
    
    # Проверка существования файла интеграции
    print("\n2. Проверка файлов интеграции:")
    try:
        from gigachat_integration import gigachat_api
        print("   ✓ Модуль gigachat_integration загружен")
    except ImportError as e:
        print(f"   ✗ Ошибка импорта: {e}")
        return False
    
    # Тестирование подключения
    print("\n3. Тестирование подключения...")
    try:
        if gigachat_api.test_connection():
            print("   ✓ Подключение к GigaChat API успешно")
            
            # Тестовая генерация
            print("\n4. Тестовая генерация плана...")
            test_data = {
                "name": "Тестовый пользователь",
                "age": 30,
                "weight": 70,
                "height": 175,
                "fitness_level": "начальный",
                "goal": "похудение",
                "health_issues": "нет"
            }
            
            prompt = "Создай базовый план тренировок для новичка."
            result = gigachat_api.generate_training_plan(test_data, prompt)
            
            if result:
                print("   ✓ Генерация успешна")
                print(f"\nРезультат (первые 300 символов):")
                print("-" * 50)
                print(result[:300] + "...")
                print("-" * 50)
                return True
            else:
                print("   ✗ Ошибка генерации")
                return False
        else:
            print("   ✗ Подключение не удалось")
            return False
            
    except Exception as e:
        print(f"   ✗ Ошибка при тестировании: {e}")
        return False

if __name__ == "__main__":
    success = run_diagnostics()
    print("\n" + "=" * 60)
    print(f"Результат диагностики: {'ПРОЙДЕНА ✅' if success else 'НЕ ПРОЙДЕНА ❌'}")
    print("=" * 60)
    sys.exit(0 if success else 1)
