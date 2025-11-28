import os
from dotenv import load_dotenv
from typing import Final

load_dotenv()

def _getenv(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Переменная окружения {name} не задана")
    return val

BOT_TOKEN: Final[str]       = _getenv("BOT_TOKEN")
TRAINER_CHAT_ID: Final[int] = int(_getenv("TRAINER_CHAT_ID"))
DB_URL: Final[str]          = _getenv("DB_URL")
OPENAI_API_KEY: Final[str]  = _getenv("OPENAI_API_KEY")