"""
Адаптер для совместимости с существующим кодом
ЗАМЕНА GigaChat API на OpenAI через ProxyAPI
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Пробуем использовать ProxyAPI
try:
    from proxy_openai_integration import generate_plan as proxy_generate_plan
    from proxy_openai_integration import generate_plan_with_edit as proxy_generate_plan_with_edit
    from proxy_openai_integration import proxy_api
    
    logger.info("✅ Используется OpenAI через ProxyAPI")
    
    # Экспортируем функции под теми же именами
    def generate_plan(data: Dict[str, Any]) -> Optional[str]:
        return proxy_generate_plan(data)
    
    def generate_plan_with_edit(data: Dict[str, Any], edit_text: str) -> Optional[str]:
        return proxy_generate_plan_with_edit(data, edit_text)
    
    # Для обратной совместимости
    gigachat_api = proxy_api
    
except ImportError as e:
    logger.error(f"❌ Ошибка импорта ProxyAPI: {e}")
    
    # Fallback на простые шаблоны
    logger.info("🔄 Используем автономные шаблоны")
    
    FALLBACK_PLANS = [
        """️ **ФИТНЕС-ПЛАН** (4 недели)

**НЕДЕЛЯ 1-2: АДАПТАЦИЯ**
- Кардио: 30 мин, 3 раза/неделю
- Силовые: приседания, отжимания, планка

**НЕДЕЛЯ 3-4: ПРОГРЕСС**
- Увеличить нагрузку на 20%
- Добавить новые упражнения""",
    ]
    
    import random
    
    def generate_plan(data: Dict[str, Any]) -> Optional[str]:
        plan = random.choice(FALLBACK_PLANS)
        personalized = f"""**ПЛАН ДЛЯ {data.get('name', 'клиента')}**

Данные:
• Возраст: {data.get('age', 'Н/Д')}
• Цели: {data.get('goals', 'общее укрепление')}
• Ограничения: {data.get('injuries', 'нет')}

{plan}"""
        return personalized
    
    def generate_plan_with_edit(data: Dict[str, Any], edit_text: str) -> Optional[str]:
        base_plan = generate_plan(data)
        return f"""**С ПРАВКАМИ ТРЕНЕРА**

{edit_text}

{base_plan}"""
    
    class DummyAPI:
        def test_connection(self):
            return False
    
    gigachat_api = DummyAPI()
