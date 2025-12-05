"""
Интеграция с OpenAI через ProxyAPI
"""

import os
import logging
from typing import Optional, Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)

class ProxyOpenAI:
    def __init__(self):
        self.api_key = os.getenv('PROXY_API_KEY')
        self.base_url = os.getenv('PROXY_API_URL', 'https://openai.api.proxyapi.ru/v1')
        self.model = os.getenv('PROXY_MODEL', 'openai/gpt-5-nano')
        
        if not self.api_key:
            logger.error("❌ PROXY_API_KEY не установлен")
            raise ValueError("PROXY_API_KEY не установлен")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=60.0
        )
        
        logger.info(f"✅ OpenAI через ProxyAPI: {self.model}")
    
    def generate_plan(self, data: Dict[str, Any]) -> Optional[str]:
        """Генерация фитнес-плана"""
        try:
            prompt = self._build_prompt(data)
            
            logger.info(f"Генерация плана для {data.get('name', 'пользователя')}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты профессиональный фитнес-тренер. Создавай безопасные и эффективные планы."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            plan = response.choices[0].message.content
            
            if plan:
                logger.info(f"✅ План сгенерирован ({len(plan)} символов)")
                return plan
            else:
                logger.error("❌ Пустой ответ")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return None
    
    def generate_plan_with_edit(self, data: Dict[str, Any], edit_text: str) -> Optional[str]:
        """Генерация с правками"""
        try:
            prompt = f"""Пересмотри фитнес-план с учетом правок тренера.

Данные клиента:
Имя: {data.get('name', 'Н/Д')}
Цели: {data.get('goals', 'Н/Д')}
Ограничения: {data.get('injuries', 'нет')}

Правки тренера: {edit_text}

Создай обновленный план."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты профессиональный фитнес-тренер."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return None
    
    def _build_prompt(self, data: Dict[str, Any]) -> str:
        """Создание промпта"""
        return f"""Создай фитнес-план на 4 недели.

Клиент: {data.get('name', 'Н/Д')}
Возраст: {data.get('age', 'Н/Д')}
Рост: {data.get('height', 'Н/Д')} см
Вес: {data.get('weight', 'Н/Д')} кг
Уровень: {data.get('fitness_level', 'начинающий')}
Цели: {data.get('goals', 'общее укрепление')}
Ограничения: {data.get('injuries', 'нет')}
Оборудование: {data.get('equipment', 'базовое')}

Требования:
1. 4 недели с прогрессией
2. Упражнения с техникой
3. Питание
4. Восстановление
5. Безопасность

Формат: Markdown"""
    
    def test_connection(self) -> bool:
        """Тест подключения"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Ответь 'OK'"}],
                max_tokens=5,
                timeout=10
            )
            return bool(response.choices[0].message.content)
        except:
            return False

# Глобальный экземпляр
openai_proxy = ProxyOpenAI()

# Функции для экспорта
def generate_plan(data: Dict[str, Any]) -> Optional[str]:
    return openai_proxy.generate_plan(data)

def generate_plan_with_edit(data: Dict[str, Any], edit_text: str) -> Optional[str]:
    return openai_proxy.generate_plan_with_edit(data, edit_text)
