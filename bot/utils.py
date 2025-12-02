import asyncpg
from aiogram import Bot
from .config import DB_URL, TRAINER_CHAT_ID, BOT_TOKEN
import aiohttp
import datetime
import os
from dotenv import load_dotenv
from typing import Dict, Optional, Any

load_dotenv()

bot_instance: Optional[Bot] = None

def get_bot() -> Bot:
    """Ленивая инициализация бота"""
    global bot_instance
    if bot_instance is None:
        bot_instance = Bot(token=BOT_TOKEN)
    return bot_instance

# --- 1. Сохранение анкеты ---
async def save_anketa(data: dict) -> None:
    conn = await asyncpg.connect(DB_URL)
    try:
        await conn.execute("""
            INSERT INTO anketa (user_id, username, name, age, height, weight, goals, injuries)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, 
        data["user_id"], 
        data.get("username"), 
        data["name"],
        int(data["age"]), 
        int(data["height"]), 
        int(data["weight"]),
        data["goals"], 
        data.get("injuries", ""))
    finally:
        await conn.close()

# --- 2. Отправка тренеру ---
async def send_to_trainer(data: dict) -> None:
    bot = get_bot()
    text = f"""
📋 Новая анкета от @{data.get('username', 'не_указан')} (ID: {data['user_id']})

Имя: {data['name']}
Возраст: {data['age']}
Рост: {data['height']} см
Вес: {data['weight']} кг
Цели: {data['goals']}
Травмы: {data.get('injuries', 'нет')}

Для генерации плана отправьте '+' или используйте /check_plan
"""
    await bot.send_message(TRAINER_CHAT_ID, text)

# --- 3. Получение JWT токена для GigaChat ---
async def get_giga_jwt() -> str:
    """Получение JWT токена"""
    # Проверяем кэшированный токен
    jwt_file = "/opt/ai-fit/.jwt"
    if os.path.exists(jwt_file):
        with open(jwt_file, "r") as f:
            token = f.read().strip()
            # Проверяем, не истёк ли токен (грубо, по времени создания файла)
            file_mtime = os.path.getmtime(jwt_file)
            if datetime.datetime.now().timestamp() - file_mtime < 3600:  # 1 час
                return token
    
    # Если токена нет или он истёк, получаем новый
    CLIENT_ID = os.getenv("GIGA_CLIENT_ID")
    if not CLIENT_ID:
        raise ValueError("GIGA_CLIENT_ID не установлен в переменных окружения")
    
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://gigachat.api.sberbank.ru/v1/token",
            headers={"Authorization": f"Bearer {CLIENT_ID}"},
            data={"scope": "GIGACHAT_API_PERS"}
        ) as resp:
            resp.raise_for_status()
            result = await resp.json()
            token = result["access_token"]
            
            # Сохраняем токен
            os.makedirs(os.path.dirname(jwt_file), exist_ok=True)
            with open(jwt_file, "w") as f:
                f.write(token)
            
            return token

# --- 4. Генерация плана (GigaChat) ---
async def generate_plan(data: Dict[str, Any]) -> str:
    """Генерация фитнес-плана через GigaChat"""
    jwt = await get_giga_jwt()
    headers = {
        "Authorization": f"Bearer {jwt}", 
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    prompt = f"""Анкета клиента:
- Имя: {data.get('name', 'не указано')}, возраст: {data.get('age', 'не указан')}
- Рост: {data.get('height', 'не указан')} см, вес: {data.get('weight', 'не указан')} кг
- Цели: {data.get('goals', 'не указаны')}
- Ограничения/травмы: {data.get('injuries', 'нет')}

Составь детальный 4-недельный план тренировок (3 раза в неделю) с рационом питания и рекомендациями по восстановлению.
Структура:
1. Тренировочная программа по неделям
2. План питания (КБЖУ, примеры блюд)
3. Рекомендации по восстановлению
4. Советы по отслеживанию прогресса"""
    
    body = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://gigachat.api.sberbank.ru/v1/chat/completions",
            headers=headers,
            json=body
        ) as resp:
            resp.raise_for_status()
            result = await resp.json()
            return result["choices"][0]["message"]["content"]

async def generate_plan_with_edit(data: Dict[str, Any], edit_text: str) -> str:
    """Генерация плана с учётом правок тренера"""
    if not edit_text or not edit_text.strip():
        raise ValueError("Текст правок не может быть пустым")
    
    # Сначала получаем исходный план
    original_plan = await generate_plan(data)
    
    jwt = await get_giga_jwt()
    headers = {
        "Authorization": f"Bearer {jwt}", 
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    prompt = f"""Исходный фитнес-план:
{original_plan}

Тренер попросил внести следующие правки:
{edit_text}

Пожалуйста, перепиши план, учитывая эти правки. Сохрани структуру плана, но внеси необходимые изменения."""
    
    body = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://gigachat.api.sberbank.ru/v1/chat/completions",
            headers=headers,
            json=body
        ) as resp:
            resp.raise_for_status()
            result = await resp.json()
            return result["choices"][0]["message"]["content"]

# --- 5. Получение последней анкеты ---
async def get_last_anketa(user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Получение последней анкеты из БД"""
    conn = await asyncpg.connect(DB_URL)
    try:
        if user_id:
            row = await conn.fetchrow(
                "SELECT * FROM anketa WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1;",
                user_id
            )
        else:
            row = await conn.fetchrow(
                "SELECT * FROM anketa ORDER BY created_at DESC LIMIT 1;"
            )
        
        if row:
            return dict(row)
        return None
    finally:
        await conn.close()

# --- 6. Сохранение плана ---
async def save_plan(data: Dict[str, Any]) -> None:
    """Сохранение плана в БД"""
    conn = await asyncpg.connect(DB_URL)
    try:
        await conn.execute("""
            INSERT INTO plans (user_id, plan_text, status, trainer_feedback, created_at) 
            VALUES ($1, $2, $3, $4, NOW());
        """, 
        data["user_id"], 
        data["plan_text"],
        data.get("status", "generated"),
        data.get("trainer_feedback"))
    finally:
        await conn.close()

# --- 7. Обновление JWT (для cron job) ---
async def refresh_jwt() -> None:
    """Обновление JWT токена (асинхронная версия)"""
    CLIENT_ID = os.getenv("GIGA_CLIENT_ID")
    if not CLIENT_ID:
        print("GIGA_CLIENT_ID не установлен")
        return
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://gigachat.api.sberbank.ru/v1/token",
            headers={"Authorization": f"Bearer {CLIENT_ID}"},
            data={"scope": "GIGACHAT_API_PERS"}
        ) as resp:
            resp.raise_for_status()
            result = await resp.json()
            jwt = result["access_token"]
            
            # Сохраняем токен
            os.makedirs("/opt/ai-fit", exist_ok=True)
            with open("/opt/ai-fit/.jwt", "w") as f:
                f.write(jwt)
            
            print(f"JWT обновлён: {datetime.datetime.now()}")