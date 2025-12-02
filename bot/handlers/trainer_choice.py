from aiogram import Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from aiogram.filters import Command
from ..utils import generate_plan, generate_plan_with_edit, get_last_anketa, save_plan, send_to_trainer
from ..config import TRAINER_CHAT_ID, BOT_TOKEN
from typing import Optional, Dict, Any

router = Router()

# Словарь для хранения ожидаемых правок от тренера
awaiting_feedback: dict[int, dict] = {}

# --- 1. Отправляем 2 кнопки тренеру ---
async def send_plan_to_trainer(data: Dict[str, Any], plan_text: str) -> None:
    """Отправка плана тренеру с кнопками"""
    from aiogram import Bot
    
    bot = Bot(token=BOT_TOKEN)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Устроил", callback_data="approve"),
            InlineKeyboardButton(text="📝 Внести правки", callback_data="edit")
        ]
    ])
    
    username = data.get('username', 'не_указан')
    user_id = data.get('user_id', 'N/A')
    
    text = f"""
📋 Черновик плана для @{username} (ID: {user_id}):

{plan_text[:1000]}...

_Нажмите кнопку ниже или напишите текст правки._
"""
    
    try:
        await bot.send_message(
            chat_id=TRAINER_CHAT_ID,
            text=text,
            reply_markup=kb
        )
    except Exception as e:
        print(f"Ошибка отправки тренеру: {e}")
    finally:
        await bot.session.close()

# --- 2. Обработка нажатия кнопки ---
@router.callback_query(lambda c: c.data in ["approve", "edit"])
async def trainer_choice(call: CallbackQuery):
    """Обработка выбора тренера"""
    if not call.message or not call.bot:
        return
    
    action = call.data
    await call.answer()  # Убираем "часики"
    
    # Получаем последнюю анкету
    data = await get_last_anketa()
    if data is None:
        await call.message.answer("Ошибка: анкета не найдена.")
        return
    
    user_id = data.get("user_id")
    if not user_id:
        await call.message.answer("Ошибка: user_id не найден в анкете.")
        return
    
    if action == "approve":
        # Генерируем план
        plan_text = await generate_plan(data)
        
        # Сохраняем план
        await save_plan({
            "user_id": user_id,
            "plan_text": plan_text,
            "status": "approved"
        })
        
        # Отправляем пользователю
        try:
            await call.bot.send_message(
                chat_id=user_id,
                text=f"✅ *Ваш персональный план утверждён!*\n\n{plan_text}\n\nПо вопросам обращайтесь к тренеру."
            )
        except Exception as e:
            await call.message.answer(f"Не удалось отправить пользователю: {e}")
        
        # Обновляем сообщение у тренера
        await call.message.edit_text(
            f"✅ План утверждён и отправлен пользователю (ID: {user_id})",
            reply_markup=None
        )
        
    elif action == "edit":
        # Запрашиваем правки
        message_id = call.message.message_id if call.message else 0
        awaiting_feedback[call.from_user.id] = {
            "message_id": message_id,
            "user_id": user_id,
            "original_data": data
        }
        
        await call.message.edit_text(
            f"✏️ *Требуются правки для пользователя ID: {user_id}*\n\n"
            f"Пожалуйста, напишите в ответ на это сообщение, что нужно изменить.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")]
            ])
        )

# --- 3. Обработка отмены правок ---
@router.callback_query(lambda c: c.data == "cancel_edit")
async def cancel_edit(call: CallbackQuery):
    """Отмена режима правок"""
    if not call.message:
        return
    
    if call.from_user.id in awaiting_feedback:
        del awaiting_feedback[call.from_user.id]
    
    await call.message.edit_text(
        "Режим правок отменён. Используйте кнопки для действий.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Устроил", callback_data="approve"),
                InlineKeyboardButton(text="📝 Внести правки", callback_data="edit")
            ]
        ])
    )
    await call.answer()

# --- 4. Обработка текста-правки ---
@router.message(lambda m: m.chat.id == TRAINER_CHAT_ID and m.text)
async def trainer_edit(message: Message):
    """Обработка текстовых правок от тренера"""
    if not message.bot or not message.chat.id:
        return
        
    if not message.from_user:
        return
    trainer_id = message.from_user.id
    
    
    # Проверяем, ожидаем ли мы правки от этого тренера
    if trainer_id not in awaiting_feedback:
        # Если это не ответ на запрос правок, игнорируем
        return
    
    feedback_data = awaiting_feedback[trainer_id]
    edit_text = message.text.strip() if message.text else ""
    
    if not edit_text or edit_text == "+":
        await message.answer("Пожалуйста, напишите конкретные правки.")
        return
    
    # Получаем оригинальные данные
    data = feedback_data.get("original_data")
    if not data:
        await message.answer("Ошибка: данные анкеты не найдены.")
        return
    
    user_id = feedback_data.get("user_id")
    if not user_id:
        await message.answer("Ошибка: ID пользователя не найден.")
        return
    
    # Генерируем план с правками
    try:
        plan_text = await generate_plan_with_edit(data, edit_text)
    except Exception as e:
        await message.answer(f"Ошибка генерации плана: {e}")
        return
    
    # Сохраняем план
    await save_plan({
        "user_id": user_id,
        "plan_text": plan_text,
        "status": "edited",
        "trainer_feedback": edit_text
    })
    
    # Отправляем обновлённый план тренеру
    await message.answer("🔄 *Обновлённый план:*\n\n" + plan_text[:1500] + "...", 
                        parse_mode="Markdown")
    
    # Отправляем пользователю
    try:
        await message.bot.send_message(
            chat_id=user_id,
            text=f"📋 *Ваш план обновлён с учётом правок тренера:*\n\n{plan_text}"
        )
    except Exception as e:
        await message.answer(f"Не удалось отправить пользователю: {e}")
    
    # Удаляем из ожидания
    del awaiting_feedback[trainer_id]
    
    # Обновляем оригинальное сообщение
    message_id = feedback_data.get("message_id")
    if message_id and message.bot:
        try:
            await message.bot.edit_message_text(
                chat_id=TRAINER_CHAT_ID,
                message_id=message_id,
                text=f"✅ Правки применены и отправлены пользователю (ID: {user_id})"
            )
        except Exception:
            pass  # Игнорируем ошибку редактирования

# --- 5. Команда для ручного запуска проверки ---
@router.message(Command("check_plan"))
async def manual_check_plan(message: Message):
    """Ручная проверка плана (для тестов)"""
    if not message.bot:
        return
        
    data = await get_last_anketa()
    if data:
        plan_text = await generate_plan(data)
        await send_plan_to_trainer(data, plan_text)
        await message.answer("План отправлен на проверку тренеру.")
    else:
        await message.answer("Нет доступных анкет для проверки.")

# --- 6. Обработка реакции "+" от тренера ---
@router.message(lambda m: m.chat.id == TRAINER_CHAT_ID and m.text == "+")
async def trainer_plus_reaction(message: Message):
    """Обработка реакции '+' от тренера"""
    if not message.bot:
        return
        
    data = await get_last_anketa()
    if not data:
        await message.answer("Ошибка: анкета не найдена.")
        return
    
    # Генерируем план
    try:
        plan_text = await generate_plan(data)
    except Exception as e:
        await message.answer(f"Ошибка генерации плана: {e}")
        return
    
    # Отправляем план тренеру для проверки
    await send_plan_to_trainer(data, plan_text)
    await message.answer("✅ План сгенерирован и отправлен на проверку.")