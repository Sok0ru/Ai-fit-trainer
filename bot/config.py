"""
Конфигурация для aiogram бота
"""

import os

# Токен бота из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# ID тренера для отправки планов на проверку
TRAINER_CHAT_ID = os.getenv('TRAINER_CHAT_ID', '')

# Настройки ProxyAPI
PROXY_API_KEY = os.getenv('PROXY_API_KEY', '')
PROXY_MODEL = os.getenv('PROXY_MODEL', 'openai/gpt-5-nano')

# Проверка обязательных переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env файле")

if not PROXY_API_KEY:
    print("⚠️  Внимание: PROXY_API_KEY не установлен. Генерация планов будет использовать fallback.")
