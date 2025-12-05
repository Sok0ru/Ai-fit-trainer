# 0. ПАТЧ DNS ДО ВСЕХ импортов, которые могут юзать requests
import socket
import requests.packages.urllib3.util.connection as conn

DNS_MAP = {
    "ngw.devices.sberbank.ru": "185.157.96.168",
    "gigachat.devices.sberbank.ru": "185.157.96.168"
}

_orig_create_connection = conn.create_connection
def patched_create_connection(address, *args, **kwargs):
    host, port = address
    host = DNS_MAP.get(host, host)
    return _orig_create_connection((host, port), *args, **kwargs)

conn.create_connection = patched_create_connection

# 1. Стандартные библиотеки – безопасно
import asyncio
import logging

# 2. aiogram – безопасно (не юзает requests)
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# 3. Наш конфиг – безопасно
from config import BOT_TOKEN

# 4. Импортируем handlers ПОСЛЕ патча
from handlers import start, anketa, trainer_choice

# 5. Остальной код
logging.basicConfig(level=logging.INFO)

async def main() -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    dp.include_router(anketa.router)
    dp.include_router(trainer_choice.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
