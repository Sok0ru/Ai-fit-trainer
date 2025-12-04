from aiogram import Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from aiogram.filters import Command
from typing import Dict, Any, Optional
import asyncio
from aiogram import Bot
from utils import generate_plan, generate_plan_with_edit, get_last_anketa, save_plan, token_refresher_task
from config import TRAINER_CHAT_ID, BOT_TOKEN

router = Router()

# Храним состояние ожидания правок
awaiting_edits: Dict[int, Dict[str, Any]] = {}

# Флаг для отслеживания запуска фоновой задачи
_token_refresher_started = False

# --- 1. Инициализация фоновой задачи ---
async def start_token_refresher():
    """Запуск фоновой задачи обновления токена"""
    global _token_refresher_started
    if not _token_refresher_started:
        _token_refresher_started = True
        asyncio.create_task(token_refresher_task())
        print("✅ Фоновая задача обновления токена запущена")

# --- 2. Отправка плана тренеру с кнопками ---
async def send_plan_to_trainer(plan_text: str, user_data: Dict[str, Any]) -> None:
    """Отправка сгенерированного плана тренеру на проверку"""
    bot = Bot(token=BOT_TOKEN)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Устроил", callback_data="approve"),
            InlineKeyboardButton(text="📝 Внести правки", callback_data="edit")
        ]
    ])
    
    username = user_data.get('username', 'не_указан')
    user_id = user_data.get('user_id', 'N/A')
    
    # Ограничиваем длину плана для телеграма
    plan_preview = plan_text[:800]
    if len(plan_text) > 800:
        plan_preview += "..."
    
    text = f"""
📋 *Черновик плана для @{username} (ID: {user_id})*

{plan_preview}

_Нажмите кнопку ниже или напишите текст правки._
"""
    
    try:
        await bot.send_message(
            chat_id=TRAINER_CHAT_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=kb
        )
    except Exception as e:
        print(f"Ошибка отправки тренеру: {e}")
    finally:
        await bot.session.close()

# --- 3. Обработка реакции "+" от тренера ---
@router.message(lambda m: m.text and m.text.strip() == "+")
async def trainer_plus_reaction(message: Message):
    """Обработка '+' для генерации плана"""
    if not message.from_user or not message.bot:
        return
    
    # Только тренер
    if message.from_user.id != TRAINER_CHAT_ID:
        return
    
    # Запускаем фоновую задачу при первом обращении
    await start_token_refresher()
    
    await message.answer("🔄 Запускаю генерацию фитнес-плана...")
    
    # Получаем последнюю анкету
    data = await get_last_anketa()
    if not data:
        await message.answer("❌ Анкета не найдена. Пользователь должен сначала заполнить анкету.")
        return
    
    try:
        # Генерируем план
        await message.answer("⏳ Обращаюсь к GigaChat API...")
        plan_text = await generate_plan(data)
        
        # Отправляем тренеру на проверку
        await send_plan_to_trainer(plan_text, data)
        
        await message.answer("✅ План сгенерирован и отправлен на проверку.")
        
    except Exception as e:
        error_msg = str(e)
        if "Client ID" in error_msg or "GIGA_CLIENT_ID" in error_msg:
            await message.answer("❌ Ошибка: GigaChat не настроен. Проверьте GIGA_CLIENT_ID в .env файле.")
        else:
            await message.answer(f"❌ Ошибка генерации плана: {error_msg[:200]}")
        print(f"Ошибка генерации плана: {e}")

# --- 4. Обработка кнопок тренера ---
@router.callback_query(lambda c: c.data in ["approve", "edit"])
async def trainer_choice(call: CallbackQuery):
    """Обработка выбора тренера (одобрить/править)"""
    if not call.message or not call.bot:
        return
    
    action = call.data
    await call.answer()
    
    # Получаем анкету
    data = await get_last_anketa()
    if not data:
        await call.message.answer("❌ Анкета не найдена.")
        return
    
    user_id = data.get("user_id")
    if not user_id:
        await call.message.answer("❌ ID пользователя не найден.")
        return
    
    if action == "approve":
        # Генерируем финальный план (или берём из сообщения)
        try:
            # Получаем текст плана из сообщения
            message_text = call.message.text or call.message.caption or ""
            
            # Ищем план в сообщении (после первой пустой строки)
            lines = message_text.split('\n')
            plan_start = 0
            for i, line in enumerate(lines):
                if line.strip() and 'черновик плана' in line.lower():
                    plan_start = i + 2  # Пропускаем заголовок и пустую строку
                    break
            
            if plan_start > 0 and plan_start < len(lines):
                plan_text = '\n'.join(lines[plan_start:])
            else:
                # Если не нашли, генерируем заново
                await call.message.answer("🔄 Генерирую финальный план...")
                plan_text = await generate_plan(data)
            
            # Сохраняем план
            await save_plan({
                "user_id": user_id,
                "plan_text": plan_text,
                "status": "approved"
            })
            
            # Отправляем пользователю
            await call.bot.send_message(
                chat_id=user_id,
                text=f"🎉 *Ваш персональный фитнес-план готов!*\n\n{plan_text}\n\n_План одобрен тренером_ ✅",
                parse_mode="Markdown"
            )
            
            # Обновляем сообщение у тренера
            await call.message.edit_text(
                f"✅ План утверждён и отправлен пользователю (ID: {user_id})",
                reply_markup=None
            )
            
        except Exception as e:
            await call.message.answer(f"❌ Ошибка: {str(e)[:200]}")
    
    elif action == "edit":
        # Запрашиваем правки
        awaiting_edits[call.from_user.id] = {
            "message_id": call.message.message_id,
            "user_id": user_id,
            "original_data": data,
            "original_plan": call.message.text or ""
        }
        
        await call.message.edit_text(
            f"✏️ *Требуются правки для пользователя ID: {user_id}*\n\n"
            "Напишите в ответ на это сообщение, что нужно изменить:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")]
            ])
        )

# --- 5. Обработка текстовых правок ---
@router.message()
async def trainer_edit(message: Message):
    """Обработка текстовых правок от тренера"""
    if not message.from_user or not message.text or not message.bot:
        return
    
    # Только тренер
    if message.from_user.id != TRAINER_CHAT_ID:
        return
    
    # Проверяем, ожидаем ли мы правки
    if message.from_user.id not in awaiting_edits:
        # Это обычное сообщение, не связанное с правками
        return
    
    edit_text = message.text.strip()
    if not edit_text or edit_text == "+":
        return
    
    feedback_data = awaiting_edits[message.from_user.id]
    data = feedback_data.get("original_data")
    user_id = feedback_data.get("user_id")
    
    if not data or not user_id:
        await message.answer("❌ Данные не найдены.")
        return
    
    await message.answer("🔄 Перерабатываю план с учётом ваших правок...")
    
    try:
        # Генерируем план с правками
        plan_text = await generate_plan_with_edit(data, edit_text)
        
        # Сохраняем план
        await save_plan({
            "user_id": user_id,
            "plan_text": plan_text,
            "status": "edited",
            "trainer_feedback": edit_text
        })
        
        # Отправляем обновлённый план тренеру с кнопками
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Устроил", callback_data="approve"),
                InlineKeyboardButton(text="📝 Внести правки", callback_data="edit")
            ]
        ])
        
        plan_preview = plan_text[:800]
        if len(plan_text) > 800:
            plan_preview += "..."
        
        await message.answer(
            f"📋 *Обновлённый план*\n\n{plan_preview}",
            parse_mode="Markdown",
            reply_markup=kb
        )
        
        # Отправляем пользователю
        await message.bot.send_message(
            chat_id=user_id,
            text=f"📋 *Ваш план обновлён с учётом правок тренера*\n\n{plan_text}",
            parse_mode="Markdown"
        )
        
        # Удаляем из ожидания
        del awaiting_edits[message.from_user.id]
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)[:200]}")
        print(f"Ошибка генерации плана с правками: {e}")

# --- 6. Отмена правок ---
@router.callback_query(lambda c: c.data == "cancel_edit")
async def cancel_edit(call: CallbackQuery):
    """Отмена режима правок"""
    if not call.message:
        return
    
    if call.from_user.id in awaiting_edits:
        del awaiting_edits[call.from_user.id]
    
    await call.message.edit_text(
        "❌ Режим правок отменён. Используйте кнопки для действий.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Устроил", callback_data="approve"),
                InlineKeyboardButton(text="📝 Внести правки", callback_data="edit")
            ]
        ])
    )
    await call.answer()

# --- 7. Команда для проверки GigaChat ---
@router.message(Command("test_giga"))
async def test_giga_command(message: Message):
    """Тестовая команда для проверки GigaChat"""
    if not message.from_user or message.from_user.id != TRAINER_CHAT_ID:
        return
    
    await start_token_refresher()
    
    test_data = {
        "name": "Иван",
        "age": "25",
        "height": "180",
        "weight": "75",
        "goals": "похудение, увеличение выносливости",
        "injuries": "нет",
        "user_id": message.from_user.id
    }
    
    await message.answer("🔄 Тестирую подключение к GigaChat API...")
    
    try:
        plan = await generate_plan(test_data)
        await message.answer(f"✅ GigaChat работает!\n\n{plan[:500]}...")
    except Exception as e:
        error_msg = str(e)
        if "Client ID" in error_msg:
            await message.answer("❌ Ошибка: GIGA_CLIENT_ID не установлен в .env файле")
        else:
            await message.answer(f"❌ Ошибка: {error_msg[:200]}")
