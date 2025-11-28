import asyncpg
from config import TRAINER_CHAT_ID, DB_URL
from aiogram import Bot
import os

bot = Bot(token=os.getenv("BOT_TOKEN"))

async def save_anketa(data):
    conn = await asyncpg.connect(DB_URL)
    await conn.execute("""
        INSERT INTO anketa (user_id, username, name, age, height, weight, goals, injuries)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """, data["user_id"], data["username"], data["name"], int(data["age"]),
       int(data["height"]), int(data["weight"]), data["goals"], data["injuries"])
    await conn.close()

async def send_to_trainer(data):
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
    await bot.send_message(TRAINER_CHAT_ID, text)