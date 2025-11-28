from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states.anketa import AnketaStates
from utils import save_anketa, send_to_trainer

router = Router()

@router.message(AnketaStates.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(AnketaStates.age)

@router.message(AnketaStates.age)
async def process_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer("Какой у тебя рост (в см)?")
    await state.set_state(AnketaStates.height)

@router.message(AnketaStates.height)
async def process_height(message: types.Message, state: FSMContext):
    await state.update_data(height=message.text)
    await message.answer("Какой у тебя вес (в кг)?")
    await state.set_state(AnketaStates.weight)

@router.message(AnketaStates.weight)
async def process_weight(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    await message.answer("Какие у тебя цели? (например: похудение, набор массы, поддержка формы)")
    await state.set_state(AnketaStates.goals)

@router.message(AnketaStates.goals)
async def process_goals(message: types.Message, state: FSMContext):
    await state.update_data(goals=message.text)
    await message.answer("Есть ли у тебя травмы или ограничения по здоровью?")
    await state.set_state(AnketaStates.injuries)

@router.message(AnketaStates.injuries)
async def process_injuries(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data["injuries"] = message.text
    data["user_id"] = message.from_user.id
    data["username"] = message.from_user.username or "Не указан"

    await save_anketa(data)
    await send_to_trainer(data)

    await message.answer("Спасибо! Твоя анкета отправлена тренеру на проверку.")
    await state.clear()