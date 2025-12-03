import os
from dotenv import load_dotenv
from typing import Final

load_dotenv()

def _getenv(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Переменная окружения {name} не задана")
    return val
# ID чата тренера
TRAINER_CHAT_ID = int(os.getenv("TRAINER_CHAT_ID", 0))
if TRAINER_CHAT_ID == 0:
    raise ValueError("TRAINER_CHAT_ID не установлен в переменных окружения")

BOT_TOKEN: Final[str]       = _getenv("BOT_TOKEN")
DB_URL: Final[str]          = _getenv("DB_URL")

# GigaChat credentials
GIGA_CLIENT_ID = os.getenv("GIGA_CLIENT_ID")
GIGA_API_URL = os.getenv("GIGA_API_URL", "https://gigachat.api.sberbank.ru/v1")
GIGA_MODEL = os.getenv("GIGA_MODEL", "GigaChat")