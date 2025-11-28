from aiogram.fsm.state import StatesGroup, State

class AnketaStates(StatesGroup):
    name = State()
    age = State()
    height = State()
    weight = State()
    goals = State()
    injuries = State()