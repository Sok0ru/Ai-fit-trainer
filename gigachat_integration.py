"""
Адаптер для совместимости: используем OpenAI через ProxyAPI
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

try:
    # Пробуем использовать OpenAI через ProxyAPI
    from proxy_openai_integration import generate_plan as proxy_generate_plan
    from proxy_openai_integration import generate_plan_with_edit as proxy_generate_plan_with_edit
    from proxy_openai_integration import openai_proxy
    
    logger.info("✅ Используется OpenAI через ProxyAPI")
    logger.info(f"   Модель: {os.getenv('PROXY_MODEL', 'openai/gpt-5-nano')}")
    logger.info("   Стоимость: ~0.15 ₽ за фитнес-план")
    
    # Перенаправляем вызовы
    def generate_plan(data: Dict[str, Any]) -> Optional[str]:
        return proxy_generate_plan(data)
    
    def generate_plan_with_edit(data: Dict[str, Any], edit_text: str) -> Optional[str]:
        return proxy_generate_plan_with_edit(data, edit_text)
    
    # Для совместимости с тестами
    gigachat_api = openai_proxy
    
except ImportError as e:
    logger.error(f"❌ Не удалось импортировать Proxy OpenAI: {e}")
    
    # Fallback на автономные шаблоны
    logger.info("🔄 Используем автономные шаблоны (fallback)")
    
    import random
    
    FALLBACK_PLANS = [
        """🏋️‍♂️ **БАЗОВЫЙ ФИТНЕС-ПЛАН** (4 недели)

**НЕДЕЛЯ 1-2: АДАПТАЦИЯ**
- Кардио: 30 мин, 3 раза/неделю
- Силовые: приседания, отжимания, планка
- Питание: белки + овощи, вода 2л

**НЕДЕЛЯ 3-4: ПРОГРЕСС**
- Увеличить нагрузку на 20%
- Добавить новые упражнения
- Следить за прогрессом""",
        
        """💪 **СБАЛАНСИРОВАННАЯ ПРОГРАММА**

**ТРЕНИРОВКИ:**
Пн: Ноги + кардио
Вт: Отдых/растяжка
Ср: Верх тела
Чт: Кардио
Пт: Фулбоди
Сб: Активный отдог
Вс: Восстановление

**ПИТАНИЕ:**
- Завтрак: белки + углеводы
- Обед: баланс БЖУ
- Ужин: легкий, белок"""
    ]
    
    def generate_plan(data: Dict[str, Any]) -> Optional[str]:
        plan = random.choice(FALLBACK_PLANS)
        personalized = f"""**ПЕРСОНАЛЬНЫЙ ПЛАН ДЛЯ {data.get('name', 'клиента')}**

📊 Данные:
• Возраст: {data.get('age', 'Н/Д')}
• Цели: {data.get('goals', 'общее укрепление')}
• Ограничения: {data.get('injuries', 'нет')}

{plan}

⚠️ Примечание: Используется базовый шаблон. Для персонализированного плана обратитесь к тренеру."""
        return personalized
    
    def generate_plan_with_edit(data: Dict[str, Any], edit_text: str) -> Optional[str]:
        base_plan = generate_plan(data)
        return f"""**ПЛАН С ПРАВКАМИ ТРЕНЕРА**

✏️ Комментарий тренера:
{edit_text}

{base_plan}"""
    
    class DummyAPI:
        def test_connection(self):
            logger.warning("⚠️ Используется fallback режим (без API)")
            return False
    
    gigachat_api = DummyAPI()
