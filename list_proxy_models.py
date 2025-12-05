#!/usr/bin/env python3
"""
Получение списка доступных моделей через ProxyAPI
"""

import os
import requests
import json

def list_available_models():
    print("=" * 70)
    print("ДОСТУПНЫЕ МОДЕЛИ PROXYAPI")
    print("=" * 70)
    
    api_key = os.getenv('PROXY_API_KEY')
    base_url = os.getenv('PROXY_API_URL', 'https://openai.api.proxyapi.ru/v1')
    
    if not api_key:
        print("❌ PROXY_API_KEY не установлен")
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{base_url}/models", headers=headers, timeout=10)
        
        if response.status_code == 200:
            models_data = response.json()
            models = models_data.get('data', [])
            
            print(f"\n📊 Найдено моделей: {len(models)}")
            print("\n🎯 РЕКОМЕНДУЕМЫЕ ДЛЯ ФИТНЕС-БОТА:")
            print("-" * 50)
            
            recommended_models = []
            
            for model in models:
                model_id = model.get('id', '')
                
                # Фильтруем интересные модели
                if any(keyword in model_id.lower() for keyword in ['gpt-5', 'gpt-4', 'claude-haiku', 'gemini-flash']):
                    recommended_models.append(model_id)
                    
                    # Выводим информацию о рекомендованных
                    if 'gpt-5-nano' in model_id:
                        print(f"🔥 {model_id} - ЛУЧШИЙ ВЫБОР! (~0.15 ₽/план)")
                    elif 'gpt-5-mini' in model_id:
                        print(f"💎 {model_id} - Качественнее (~0.80 ₽/план)")
                    elif 'gpt-4.1-nano' in model_id:
                        print(f"⚡ {model_id} - Надежный (~0.18 ₽/план)")
                    elif 'claude-haiku' in model_id:
                        print(f"🤖 {model_id} - Альтернатива (~2.38 ₽/план)")
                    elif 'gemini-2.5-flash-lite' in model_id:
                        print(f"🌐 {model_id} - Google модель (~0.15 ₽/план)")
            
            print("\n📋 ВСЕ ДОСТУПНЫЕ МОДЕЛИ:")
            print("-" * 50)
            
            # Группируем по провайдерам
            providers = {}
            for model in models:
                model_id = model.get('id', '')
                if '/' in model_id:
                    provider = model_id.split('/')[0]
                    if provider not in providers:
                        providers[provider] = []
                    providers[provider].append(model_id)
            
            for provider, model_list in providers.items():
                print(f"\n{provider.upper()}:")
                for model_id in sorted(model_list)[:5]:  # Показываем первые 5
                    print(f"  • {model_id}")
                if len(model_list) > 5:
                    print(f"  • ... и еще {len(model_list) - 5} моделей")
                    
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == '__main__':
    list_available_models()
