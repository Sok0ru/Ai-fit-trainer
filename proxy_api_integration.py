"""
Интеграция с Proxy API (посредник для OpenAI/Claude/Gemini)
"""

import os
import json
import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class ProxyAPI:
    """Универсальный клиент для Proxy API"""
    
    def __init__(self):
        # Конфигурация из переменных окружения
        self.api_key = os.getenv('PROXY_API_KEY')
        self.base_url = os.getenv('PROXY_API_URL', 'https://api.proxyapi.ru/openai/v1')
        self.model = os.getenv('PROXY_MODEL', 'gpt-5-nano')  # GPT-5-nano - оптимальный выбор
        
        if not self.api_key:
            logger.error("❌ PROXY_API_KEY не установлен")
            raise ValueError("PROXY_API_KEY не установлен")
        
        # Настройка сессии
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        
        logger.info(f"✅ Proxy API настроен (модель: {self.model})")
    
    def generate_plan(self, data: Dict[str, Any]) -> Optional[str]:
        """Генерация фитнес-плана"""
        try:
            prompt = self._build_prompt(data)
            
            logger.info(f"Генерация плана для {data.get('name', 'пользователя')} через {self.model}...")
            
            response = self._call_api(prompt)
            
            if response:
                logger.info(f"✅ План успешно сгенерирован ({len(response)} символов)")
                return response
            else:
                logger.error("❌ Не удалось сгенерировать план")
                return None
                
        except Exception as e:
            logger.error(f"⚠️ Ошибка генерации плана: {e}")
            return None
    
    def generate_plan_with_edit(self, data: Dict[str, Any], edit_text: str) -> Optional[str]:
        """Генерация плана с правками тренера"""
        try:
            prompt = self._build_prompt_with_edit(data, edit_text)
            
            logger.info(f"Генерация плана с правками через {self.model}...")
            
            response = self._call_api(prompt)
            
            if response:
                logger.info(f"✅ План с правками успешно сгенерирован ({len(response)} символов)")
                return response
            else:
                logger.error("❌ Не удалось сгенерировать план с правками")
                return None
                
        except Exception as e:
            logger.error(f"⚠️ Ошибка генерации плана с правками: {e}")
            return None
    
    def _call_api(self, prompt: str) -> Optional[str]:
        """Вызов Proxy API"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2500,  # Экономим токены
            "top_p": 0.9
        }
        
        try:
            response = self.session.post(
                url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                message_content = result.get('choices', [{}])[0].get('message', {}).get('content')
                
                # Логируем использование токенов для контроля стоимости
                usage = result.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                
                logger.info(f"📊 Использовано токенов: {prompt_tokens} prompt + {completion_tokens} completion")
                self._log_cost_estimate(prompt_tokens, completion_tokens)
                
                return message_content
            else:
                logger.error(f"❌ Ошибка API: {response.status_code}")
                logger.error(f"Ответ: {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("⏱️ Таймаут при обращении к API")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("🔌 Ошибка подключения к API")
            return None
        except Exception as e:
            logger.error(f"⚠️ Неожиданная ошибка: {e}")
            return None
    
    def _build_prompt(self, data: Dict[str, Any]) -> str:
        """Оптимизированный промпт для экономии токенов"""
        return f"""Создай фитнес-план на 4 недели.

Клиент: {data.get('name', 'Н/Д')}
Возраст: {data.get('age', 'Н/Д')}
Рост: {data.get('height', 'Н/Д')} см
Вес: {data.get('weight', 'Н/Д')} кг
Уровень: {data.get('fitness_level', 'начинающий')}
Цели: {data.get('goals', 'общее укрепление')}
Ограничения: {data.get('injuries', 'нет')}

Требования:
1. 4 недели с прогрессией
2. Упражнения с техникой
3. Питание
4. Восстановление
5. Меры безопасности

Формат: Markdown, кратко, по делу."""
    
    def _build_prompt_with_edit(self, data: Dict[str, Any], edit_text: str) -> str:
        """Промпт с правками тренера"""
        return f"""Пересмотри фитнес-план с учетом правок тренера.

Клиент: {data.get('name', 'Н/Д')}
Цели: {data.get('goals', 'общее укрепление')}
Ограничения: {data.get('injuries', 'нет')}

Правки тренера: {edit_text}

Создай обновленный план. Формат: Markdown, кратко."""
    
    def _get_system_prompt(self) -> str:
        """Оптимизированный системный промпт"""
        return """Ты опытный фитнес-тренер. Создавай безопасные, эффективные планы.
Будь кратким, но информативным. Используй Markdown."""
    
    def _log_cost_estimate(self, prompt_tokens: int, completion_tokens: int):
        """Логирование примерной стоимости запроса"""
        # Примерные цены для моделей (в рублях за 1K токенов)
        prices = {
            'gpt-5-nano': {'input': 12.24, 'output': 97.92},
            'gpt-5-mini': {'input': 61.20, 'output': 489.60},
            'gpt-4.1-nano': {'input': 24.48, 'output': 97.92},
            'gpt-4.1-mini': {'input': 97.92, 'output': 391.68},
        }
        
        if self.model in prices:
            price = prices[self.model]
            cost = (prompt_tokens / 1000 * price['input']) + (completion_tokens / 1000 * price['output'])
            logger.info(f"💰 Примерная стоимость: {cost:.2f} ₽")
        else:
            logger.info(f"💰 Модель {self.model} - проверьте тарифы")
    
    def test_connection(self) -> bool:
        """Тестирование подключения"""
        try:
            logger.info(f"Тестируем подключение к Proxy API ({self.model})...")
            
            # Простой тестовый запрос
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Ответь 'OK'"}],
                "max_tokens": 5
            }
            
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            
            success = response.status_code == 200
            if success:
                logger.info("✅ Proxy API доступен")
            else:
                logger.error(f"❌ Ошибка API: {response.status_code}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования: {e}")
            return False

# Глобальный экземпляр
proxy_api = ProxyAPI()

# Алиасы для совместимости
def generate_plan(data: Dict[str, Any]) -> Optional[str]:
    return proxy_api.generate_plan(data)

def generate_plan_with_edit(data: Dict[str, Any], edit_text: str) -> Optional[str]:
    return proxy_api.generate_plan_with_edit(data, edit_text)
