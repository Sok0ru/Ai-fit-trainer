#!/usr/bin/env python3
import os
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_gigachat_auth():
    """Отладка аутентификации GigaChat"""
    
    print("=" * 70)
    print("ОТЛАДКА АУТЕНТИФИКАЦИИ GIGACHAT")
    print("=" * 70)
    
    # Получаем API ключ
    api_key = os.getenv('GIGACHAT_API_KEY')
    if not api_key:
        print("❌ GIGACHAT_API_KEY не установлен")
        return
    
    print(f"\n1. API ключ получен:")
    print(f"   Длина: {len(api_key)} символов")
    print(f"   Начинается с 'Bearer': {api_key.startswith('Bearer ')}")
    
    if not api_key.startswith('Bearer '):
        print("   ⚠️  Добавляем 'Bearer ' префикс...")
        api_key = f'Bearer {api_key}'
    
    print(f"\n2. Пробуем получить access token...")
    
    auth_url = os.getenv('GIGACHAT_AUTH_URL', 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth')
    
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    
    data = {'scope': 'GIGACHAT_API_PERS'}
    
    try:
        print(f"   URL: {auth_url}")
        print(f"   Headers: Authorization: {api_key[:40]}...")
        
        response = requests.post(
            auth_url,
            headers=headers,
            data=data,
            timeout=30,
            verify=True
        )
        
        print(f"\n3. Ответ от сервера аутентификации:")
        print(f"   Статус код: {response.status_code}")
        print(f"   Заголовки: {dict(response.headers)}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"\n✅ Успешная аутентификация!")
            print(f"   Access token получен: {'access_token' in token_data}")
            print(f"   Токен действителен: {token_data.get('expires_in', 'N/A')} секунд")
            
            # Пробуем использовать токен
            access_token = token_data.get('access_token')
            if access_token:
                print(f"\n4. Тестируем вызов API с полученным токеном...")
                
                api_url = os.getenv('GIGACHAT_API_URL', 'https://gigachat.devices.sberbank.ru/api/v1')
                chat_url = f"{api_url}/chat/completions"
                
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                
                payload = {
                    "model": "GigaChat",
                    "messages": [
                        {
                            "role": "user", 
                            "content": "Привет! Ответь одним словом."
                        }
                    ],
                    "max_tokens": 10
                }
                
                response = requests.post(
                    chat_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                print(f"   Статус API вызова: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ API работает! Ответ: {result}")
                else:
                    print(f"   ❌ API ошибка: {response.text}")
            
        elif response.status_code == 401:
            print(f"\n❌ ОШИБКА 401: Неавторизован")
            print("   Возможные причины:")
            print("   1. API ключ недействителен")
            print("   2. API ключ просрочен")
            print("   3. Неправильный формат ключа")
            print("   4. Нет доступа к GigaChat API")
            print(f"\n   Ответ сервера: {response.text}")
            
        elif response.status_code == 400:
            print(f"\n❌ ОШИБКА 400: Неправильный запрос")
            print(f"   Ответ: {response.text}")
            
        else:
            print(f"\n⚠️  Неожиданный статус: {response.status_code}")
            print(f"   Ответ: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Исключение: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_gigachat_auth()
