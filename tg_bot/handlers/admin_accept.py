import re

from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, CallbackQuery
from icecream import ic

from bot.models import Certification, File
from dispatcher import dp
from tg_bot.buttons.inline import accept, reply_payment
from tg_bot.buttons.reply import *
# from tg_bot.handlers.admin import *
from tg_bot.state.main import *
from tg_bot.test import format_phone_number


@dp.message(lambda msg: msg.text == "/start")
async def command_start_handler(message: Message, state: FSMContext) -> None:
    pass


@dp.message(StateFilter(Messeage.full_name))
async def handle_phone_number(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    data['full_name'] = message.text
    await state.set_data(data)
    await state.set_state(Messeage.photo)
    await message.answer("Shaxsiy rasmingizni yuklang:", reply_markup=back())
