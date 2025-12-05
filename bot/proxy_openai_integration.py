"""
OpenAI через ProxyAPI для генерации фитнес-планов
Используется официальный OpenAI SDK
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
        logger.info(f"💰 Стоимость: ~0.15 ₽ за фитнес-план")
    
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
                        "content": self._get_system_prompt()
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
                # Логируем использование
                usage = response.usage
                if usage:
                    prompt_tokens = usage.prompt_tokens
                    completion_tokens = usage.completion_tokens
                    cost = self._estimate_cost(prompt_tokens, completion_tokens)
                    
                    logger.info(f"✅ План сгенерирован ({len(plan)} символов)")
                    logger.info(f"📊 Токены: {prompt_tokens} prompt, {completion_tokens} completion")
                    logger.info(f"💰 Стоимость: {cost:.3f} ₽")
                else:
                    logger.info(f"✅ План сгенерирован ({len(plan)} символов)")
                
                return plan
            else:
                logger.error("❌ Пустой ответ от API")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации плана: {e}")
            return None
    
    def generate_plan_with_edit(self, data: Dict[str, Any], edit_text: str) -> Optional[str]:
        """Генерация плана с правками тренера"""
        try:
            prompt = self._build_prompt_with_edit(data, edit_text)
            
            logger.info(f"Генерация плана с правками...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
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
                logger.info(f"✅ План с правками сгенерирован ({len(plan)} символов)")
                return plan
            else:
                logger.error("❌ Пустой ответ от API")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации плана с правками: {e}")
            return None
    
    def _build_prompt(self, data: Dict[str, Any]) -> str:
        """Создание промпта для фитнес-плана"""
        return f"""Создай подробный персонализированный фитнес-план на 4 недели.

👤 ДАННЫЕ КЛИЕНТА:
• Имя: {data.get('name', 'Клиент')}
• Возраст: {data.get('age', 'Не указан')}
• Рост: {data.get('height', 'Не указан')} см
• Вес: {data.get('weight', 'Не указан')} кг
• Уровень подготовки: {data.get('fitness_level', 'Начинающий')}
• Цели: {data.get('goals', 'Общее укрепление здоровья')}
• Ограничения/травмы: {data.get('injuries', 'Нет')}

🎯 ТРЕБОВАНИЯ К ПЛАНУ:
1. 4 недели с прогрессией нагрузок
2. Подробное расписание тренировок
3. Конкретные упражнения с техникой
4. Рекомендации по питанию
5. Советы по восстановлению
6. Меры предосторожности

📝 ФОРМАТ: Используй Markdown, будь структурированным и мотивирующим."""
    
    def _build_prompt_with_edit(self, data: Dict[str, Any], edit_text: str) -> str:
        """Промпт для плана с правками"""
        return f"""Пересмотри фитнес-план с учетом правок тренера.

👤 ДАННЫЕ КЛИЕНТА:
• Имя: {data.get('name', 'Клиент')}
• Цели: {data.get('goals', 'Общее укрепление')}
• Ограничения: {data.get('injuries', 'Нет')}

✏️ ПРАВКИ ТРЕНЕРА:
{edit_text}

🎯 ЗАДАЧА:
1. Учти все правки тренера
2. Создай обновленный план
3. Сохрани безопасность и эффективность

📝 ФОРМАТ: Markdown, с обоснованием изменений."""
    
    def _get_system_prompt(self) -> str:
        """Системный промпт"""
        return """Ты профессиональный фитнес-тренер с медицинским образованием.
Твои принципы: безопасность, индивидуальный подход, научная обоснованность.
Создавай персонализированные, мотивирующие и эффективные планы тренировок."""
    
    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Оценка стоимости в рублях"""
        model_name = self.model.split('/')[-1] if '/' in self.model else self.model
        
        # Цены за 1 МИЛЛИОН токенов
        prices = {
            'gpt-5-nano': {'input': 12.24, 'output': 97.92},
            'gpt-5-mini': {'input': 61.20, 'output': 489.60},
            'gpt-4.1-nano': {'input': 24.48, 'output': 97.92},
        }
        
        if model_name in prices:
            price = prices[model_name]
            cost = (prompt_tokens / 1_000_000 * price['input']) + \
                   (completion_tokens / 1_000_000 * price['output'])
            return round(cost, 4)
        
        return 0.15  # Примерная стоимость
    
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

# Глобальный экземпляр для использования в других модулях
proxy_api = ProxyOpenAI()

# Функции для экспорта (для совместимости)
def generate_plan(data: Dict[str, Any]) -> Optional[str]:
    return proxy_api.generate_plan(data)

def generate_plan_with_edit(data: Dict[str, Any], edit_text: str) -> Optional[str]:
    return proxy_api.generate_plan_with_edit(data, edit_text)