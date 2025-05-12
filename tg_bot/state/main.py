from aiogram.fsm.state import StatesGroup, State


class User(StatesGroup):
    lang = State()
    phone = State()
