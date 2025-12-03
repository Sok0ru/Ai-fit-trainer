# utils.py - объединённая версия
import asyncpg
from aiogram import Bot
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

bot_instance: Optional[Bot] = None

def get_bot() -> Optional[Bot]:
    """Ленивая инициализация бота"""
    global bot_instance
    if bot_instance is None:
        from config import BOT_TOKEN
        if not BOT_TOKEN:
            return None
        bot_instance = Bot(token=BOT_TOKEN)
    return bot_instance

# --- 1. Класс GigaChatAuth внутри utils.py ---
class GigaChatAuth:
    def __init__(self, client_id: str, auth_url: str = "https://gigachat.api.sberbank.ru/v1/token"):
        self.client_id = client_id
        self.auth_url = auth_url
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        self._lock = asyncio.Lock()
    
    async def get_token(self) -> Optional[str]:
        """Получение JWT токена с кэшированием"""
        async with self._lock:
            # Проверяем, не истёк ли текущий токен
            if self._token and self._token_expires and datetime.now() < self._token_expires:
                return self._token
            
            # Получаем новый токен
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.client_id}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                data = {"scope": "GIGACHAT_API_PERS"}
                
                async with session.post(self.auth_url, headers=headers, data=data) as response:
                    response.raise_for_status()
                    result = await response.json()
                    
                    self._token = result["access_token"]
                    # Токен живёт 30 минут, ставим 25 для запаса
                    self._token_expires = datetime.now() + timedelta(minutes=25)
                    
                    print(f"✅ JWT токен получен, истекает в {self._token_expires.strftime('%H:%M:%S')}")
                    return self._token

# --- 2. Инициализация аутентификации ---
from config import GIGA_CLIENT_ID
giga_auth: Optional[GigaChatAuth] = None

if GIGA_CLIENT_ID:
    giga_auth = GigaChatAuth(GIGA_CLIENT_ID)
    print("✅ GigaChatAuth инициализирован")
else:
    print("⚠️ GIGA_CLIENT_ID не установлен, GigaChat недоступен")

# --- 3. Работа с базой данных ---
async def save_anketa(data: Dict[str, Any]) -> None:
    """Сохранение анкеты в БД"""
    from config import DB_URL
    
    conn = await asyncpg.connect(DB_URL)
    try:
        await conn.execute("""
            INSERT INTO anketa (user_id, username, name, age, height, weight, goals, injuries, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
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

async def get_last_anketa(user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Получение последней анкеты из БД"""
    from config import DB_URL
    
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

async def save_plan(data: Dict[str, Any]) -> None:
    """Сохранение плана в БД"""
    from config import DB_URL
    
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

# --- 4. Генерация плана через GigaChat ---
def create_fitness_prompt(user_data: Dict[str, Any]) -> str:
    """Создание промпта для генерации фитнес-плана"""
    return f"""
Создай подробный персонализированный фитнес-план на основе данных пользователя:

👤 О пользователе:
- Имя: {user_data.get('name', 'Не указано')}
- Возраст: {user_data.get('age', 'Не указан')}
- Рост: {user_data.get('height', 'Не указан')} см
- Вес: {user_data.get('weight', 'Не указан')} кг
- Цели: {user_data.get('goals', 'Не указаны')}
- Ограничения/травмы: {user_data.get('injuries', 'Нет')}

🎯 Структура плана (используй Markdown разметку):

## 1. ТРЕНИРОВОЧНАЯ ПРОГРАММА (4 недели)
### Неделя 1-2: Адаптация
- Расписание тренировок (3-4 раза в неделю)
- Упражнения с подходами и повторениями
- Интенсивность и время отдыха

### Неделя 3-4: Прогрессия
- Увеличение нагрузок
- Новые упражнения
- Методики прогрессии

## 2. ПЛАН ПИТАНИЯ
### Рекомендации по КБЖУ:
- Калории: подходящая калорийность
- Белки, жиры, углеводы: соотношение

### Примерный рацион на день:
- Завтрак, обед, ужин, перекусы

### Режим питания:
- Частота приёмов пищи
- Время питания
- Гидратация

## 3. РЕКОМЕНДАЦИИ
### Восстановление:
- Сон (количество часов)
- Растяжка
- Отдых между тренировками

### Отслеживание прогресса:
- Замеры (что и как часто измерять)
- Дневник тренировок

План должен быть практичным, мотивирующим и учитывать индивидуальные особенности.
"""

async def generate_plan(user_data: Dict[str, Any]) -> str:
    """Генерация фитнес-плана через GigaChat"""
    if not giga_auth:
        raise Exception("GigaChat не настроен. Проверьте GIGA_CLIENT_ID в .env")
    
    try:
        # Получаем токен
        token = await giga_auth.get_token()
        if not token:
            raise Exception("Не удалось получить токен GigaChat")
        
        # Формируем промпт
        prompt = create_fitness_prompt(user_data)
        
        # Отправляем запрос
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "GigaChat",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты профессиональный фитнес-тренер и диетолог. Составь персонализированный план тренировок и питания. Отвечай на русском языке, используй Markdown для форматирования."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            async with session.post(
                "https://gigachat.api.sberbank.ru/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"GigaChat API error {response.status}: {error_text}")
                
                result = await response.json()
                return result["choices"][0]["message"]["content"]
                
    except Exception as e:
        print(f"❌ Ошибка генерации плана: {e}")
        raise

async def generate_plan_with_edit(user_data: Dict[str, Any], edit_text: str) -> str:
    """Генерация плана с учётом правок тренера"""
    if not giga_auth:
        raise Exception("GigaChat не настроен")
    
    # Получаем токен
    token = await giga_auth.get_token()
    if not token:
        raise Exception("Не удалось получить токен GigaChat")
    
    # Формируем промпт с правками
    prompt = f"""
На основе следующих данных пользователя создай фитнес-план:

Имя: {user_data.get('name', 'Не указано')}
Возраст: {user_data.get('age', 'Не указан')}
Рост: {user_data.get('height', 'Не указан')} см
Вес: {user_data.get('weight', 'Не указан')} кг
Цели: {user_data.get('goals', 'Не указаны')}
Ограничения: {user_data.get('injuries', 'Нет')}

Комментарии тренера для исправления:
{edit_text}

Пожалуйста, создай подробный фитнес-план с учётом этих замечаний.
Включи: тренировочную программу на 4 недели, план питания, рекомендации.
Используй Markdown для форматирования.
"""
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "GigaChat",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            async with session.post(
                "https://gigachat.api.sberbank.ru/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"❌ Ошибка генерации плана с правками: {e}")
        raise

# --- 5. Отправка тренеру ---
async def send_to_trainer(data: Dict[str, Any]) -> None:
    """Отправка анкеты тренеру"""
    bot = get_bot()
    if not bot:
        print("❌ Бот не инициализирован")
        return
    
    from config import TRAINER_CHAT_ID
    
    text = f"""
📋 Новая анкета от @{data.get('username', 'не_указан')} (ID: {data['user_id']})

Имя: {data['name']}
Возраст: {data['age']}
Рост: {data['height']} см
Вес: {data['weight']} кг
Цели: {data['goals']}
Травмы: {data.get('injuries', 'нет')}

Отправьте '+' чтобы сгенерировать план.
"""
    await bot.send_message(TRAINER_CHAT_ID, text)

# --- 6. Фоновая задача для обновления токена ---
async def token_refresher_task():
    """Фоновая задача для периодического обновления токена"""
    if not giga_auth:
        return
    
    while True:
        try:
            # Обновляем токен каждые 20 минут
            await asyncio.sleep(20 * 60)
            token = await giga_auth.get_token()
            if token:
                print(f"✅ Токен обновлён в фоне")
            else:
                print("⚠️ Не удалось обновить токен")
        except Exception as e:
            print(f"Ошибка обновления токена: {e}")
            await asyncio.sleep(60)