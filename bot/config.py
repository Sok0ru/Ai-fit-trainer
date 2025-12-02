import os
from dotenv import load_dotenv
from typing import Final

load_dotenv()

def _getenv(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Переменная окружения {name} не задана")
    return val
# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в переменных окружения")

# ID чата тренера
TRAINER_CHAT_ID = int(os.getenv("TRAINER_CHAT_ID", 0))
if TRAINER_CHAT_ID == 0:
    raise ValueError("TRAINER_CHAT_ID не установлен в переменных окружения")

# URL базы данных
DB_URL = os.getenv("DB_URL", "postgresql://user:password@localhost/fitness_bot")

# GigaChat credentials
GIGA_CLIENT_ID = os.getenv("GIGA_CLIENT_ID")