import asyncio
import os
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import start, anketa
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(start.router)
    dp.include_router(anketa.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())