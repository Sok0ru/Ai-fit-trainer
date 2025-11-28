import asyncpg
from aiogram import Bot
from config import DB_URL, TRAINER_CHAT_ID, BOT_TOKEN   # ←

bot = Bot(token=BOT_TOKEN)                               # ← str

async def save_anketa(data: dict) -> None:
    conn = await asyncpg.connect(DB_URL)
    await conn.execute("""
        INSERT INTO anketa (user_id, username, name, age, height, weight, goals, injuries)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, data["user_id"], data["username"], data["name"],
       int(data["age"]), int(data["height"]), int(data["weight"]),
       data["goals"], data["injuries"])
    await conn.close()

async def send_to_trainer(data: dict) -> None:
    text = f"""
📋 Новая анкета от @{data['username']} (ID: {data['user_id']})

Имя: {data['name']}
Возраст: {data['age']}
Рост: {data['height']} см
Вес: {data['weight']} кг
Цели: {data['goals']}
Травмы: {data['injuries']}

Отправьте '+' чтобы подтвердить, или напишите правки.
"""
    await bot.send_message(TRAINER_CHAT_ID, text)   # ← int, а не str | None