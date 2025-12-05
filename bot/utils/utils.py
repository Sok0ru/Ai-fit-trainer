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

# ---------- переадресация в SDK ----------
from gigachat_integration import generate_plan as _sdk_generate_plan
from gigachat_integration import generate_plan_with_edit as _sdk_generate_plan_with_edit

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

# ---------- БАЗОВЫЕ ФУНКЦИИ (без изменений) ----------
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
        logger.info("✅ План сохранён")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения плана: {e}")

# ---------- GIGACHAT (переадресация в SDK) ----------
async def generate_plan(user_data: Dict[str, Any]) -> str:
    """Генерация плана через официальный SDK GigaChat"""
    return await asyncio.to_thread(_sdk_generate_plan, user_data)


async def generate_plan_with_edit(user_data: Dict[str, Any], edit_text: str) -> str:
    """Генерация плана с учётом правок тренера"""
    return await asyncio.to_thread(_sdk_generate_plan_with_edit, user_data, edit_text)


async def token_refresher_task():
    """Фоновая задача обновления токена (не используется, но оставим для совместимости)"""
    while True:
        await asyncio.sleep(20 * 60)
        logger.info("🔁 Фоновое обновление токена (заглушка)")
