import asyncpg
from aiogram import Bot
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

# Telegram бот
bot_instance: Optional[Bot] = None

def get_bot() -> Optional[Bot]:
    global bot_instance
    if bot_instance is None:
        from config import BOT_TOKEN
        if not BOT_TOKEN:
            return None
        bot_instance = Bot(token=BOT_TOKEN)
    return bot_instance

# === БАЗОВЫЕ ФУНКЦИИ (работают всегда) ===
async def save_anketa(data: Dict[str, Any]) -> None:
    """Сохранение анкеты в БД"""
    from config import DB_URL
    try:
        conn = await asyncpg.connect(DB_URL)
        await conn.execute("""
            INSERT INTO anketa (user_id, username, name, age, height, weight, goals, injuries, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
        """, 
        data.get("user_id"), 
        data.get("username", ""), 
        data.get("name", ""),
        int(data.get("age", 0)), 
        int(data.get("height", 0)), 
        int(data.get("weight", 0)),
        data.get("goals", ""), 
        data.get("injuries", ""))
        await conn.close()
        logger.info(f"✅ Анкета сохранена: {data.get('name')}")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения анкеты: {e}")

async def send_to_trainer(data: Dict[str, Any]) -> None:
    """Отправка анкеты тренеру"""
    bot = get_bot()
    if not bot:
        logger.error("❌ Бот не инициализирован")
        return
    
    from config import TRAINER_CHAT_ID
    
    text = f"""
📋 Новая анкета от @{data.get('username', 'не_указан')} (ID: {data.get('user_id', 'N/A')})

Имя: {data.get('name', 'Не указано')}
Возраст: {data.get('age', 'Не указан')}
Рост: {data.get('height', 'Не указан')} см
Вес: {data.get('weight', 'Не указан')} кг
Цели: {data.get('goals', 'Не указаны')}
Травмы: {data.get('injuries', 'Нет')}

Отправьте '+' чтобы сгенерировать план.
"""
    try:
        await bot.send_message(TRAINER_CHAT_ID, text)
        logger.info("✅ Анкета отправлена тренеру")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки тренеру: {e}")

async def get_last_anketa(user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Получение последней анкеты"""
    from config import DB_URL
    try:
        conn = await asyncpg.connect(DB_URL)
        if user_id:
            row = await conn.fetchrow(
                "SELECT * FROM anketa WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1;",
                user_id
            )
        else:
            row = await conn.fetchrow(
                "SELECT * FROM anketa ORDER BY created_at DESC LIMIT 1;"
            )
        await conn.close()
        if row:
            return dict(row)
    except Exception as e:
        logger.error(f"❌ Ошибка БД: {e}")
    return None

async def save_plan(data: Dict[str, Any]) -> None:
    """Сохранение плана в БД"""
    from config import DB_URL
    try:
        conn = await asyncpg.connect(DB_URL)
        await conn.execute("""
            INSERT INTO plans (user_id, plan_text, status, trainer_feedback, created_at) 
            VALUES ($1, $2, $3, $4, NOW());
        """, 
        data.get("user_id"), 
        data.get("plan_text", ""),
        data.get("status", "generated"),
        data.get("trainer_feedback", ""))
        await conn.close()
        logger.info(f"✅ План сохранён")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения плана: {e}")

# === GIGACHAT ФУНКЦИИ ===
class GigaChatAuth:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
    
    async def get_token(self) -> Optional[str]:
        """Получение токена GigaChat"""
        from config import GIGA_CLIENT_ID
        if not GIGA_CLIENT_ID:
            raise Exception("GIGA_CLIENT_ID не установлен в .env")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://gigachat.api.sberbank.ru/v1/token",
                    headers={"Authorization": f"Bearer {self.client_id}"},
                    data={"scope": "GIGACHAT_API_PERS"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    result = await response.json()
                    self._token = result["access_token"]
                    self._token_expires = datetime.now() + timedelta(minutes=25)
                    return self._token
        except Exception as e:
            logger.error(f"❌ Ошибка получения токена: {e}")
            raise

# Глобальный экземпляр GigaChat
giga_auth = None
from config import GIGA_CLIENT_ID
if GIGA_CLIENT_ID:
    try:
        giga_auth = GigaChatAuth(GIGA_CLIENT_ID)
        logger.info("✅ GigaChatAuth инициализирован")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации GigaChat: {e}")

async def generate_plan(user_data: Dict[str, Any]) -> str:
    """Генерация плана через GigaChat"""
    if not GIGA_CLIENT_ID:
        return """📋 Тестовый фитнес-план
    
🎯 На основе ваших целей создан персонализированный план.

**Тренировки:**
- Пн: Кардио 30 мин + Силовая тренировка
- Ср: Йога/Растяжка 40 мин  
- Пт: Интервальная тренировка 45 мин

**Питание:**
- Завтрак: Белки + сложные углеводы
- Обед: Овощи + мясо/рыба
- Ужин: Лёгкий белок + овощи

💡 Для реальной генерации добавьте GIGA_CLIENT_ID в .env"""
    
    if not giga_auth:
        raise Exception("GigaChat не инициализирован")
    
    try:
        # Получаем токен
        token = await giga_auth.get_token()
        
        # Формируем промпт
        prompt = f"""Создай детальный фитнес-план на 4 недели.

Данные пользователя:
- Имя: {user_data.get('name', 'Не указано')}
- Возраст: {user_data.get('age', 'Не указан')}
- Рост: {user_data.get('height', 'Не указан')} см
- Вес: {user_data.get('weight', 'Не указан')} кг
- Цели: {user_data.get('goals', 'Не указаны')}
- Ограничения: {user_data.get('injuries', 'Нет')}

Включи:
1. Тренировочную программу по неделям
2. План питания с КБЖУ
3. Рекомендации по восстановлению
4. Советы по отслеживанию прогресса

Используй Markdown для форматирования."""
        
        # Отправляем запрос с таймаутом
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://gigachat.api.sberbank.ru/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "GigaChat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1500
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"API error {response.status}: {error[:100]}")
                
                result = await response.json()
                return result["choices"][0]["message"]["content"]
                
    except asyncio.TimeoutError:
        raise Exception("Таймаут подключения к GigaChat API. Проверьте сеть.")
    except aiohttp.ClientConnectorError:
        raise Exception("Не удалось подключиться к GigaChat API. Проверьте сетевые настройки.")
    except Exception as e:
        logger.error(f"❌ Ошибка GigaChat: {e}")
        raise Exception(f"Ошибка генерации плана: {str(e)[:100]}")

async def generate_plan_with_edit(user_data: Dict[str, Any], edit_text: str) -> str:
    """Генерация плана с правками"""
    try:
        return await generate_plan(user_data)
    except Exception as e:
        return f"📝 Не удалось перегенерировать план. Ошибка: {str(e)[:200]}"

async def token_refresher_task():
    """Фоновая задача обновления токена"""
    if not giga_auth:
        return
    
    while True:
        try:
            await asyncio.sleep(20 * 60)  # 20 минут
            await giga_auth.get_token()
            logger.info("✅ Токен GigaChat обновлён")
        except Exception as e:
            logger.error(f"❌ Ошибка обновления токена: {e}")
            await asyncio.sleep(60)
