from aiogram import Router, types
from aiogram.filters import CommandStart
from ..states.anketa import AnketaStates
from aiogram.fsm.context import FSMContext
router = Router()

@router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    await message.answer("Привет! Я — ИИ-тренер. Давай начнем с анкеты. Как тебя зовут?")
    await state.set_state(AnketaStates.name)   
    