import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
TRAINER_CHAT_ID = int(os.getenv("TRAINER_CHAT_ID", 0))

# Database
DB_URL = os.getenv("DB_URL", "postgresql://bot:strongpass@postgres/fitbot")

# GigaChat
GIGA_CLIENT_ID = os.getenv("GIGA_CLIENT_ID")
