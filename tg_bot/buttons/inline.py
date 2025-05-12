from aiofiles.os import access

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async

from tg_bot.buttons.text import ortga
from tg_bot.utils.translator import get_text


def choose_language():
    en = InlineKeyboardButton(text='🇬🇧 English', callback_data='en')
    ru = InlineKeyboardButton(text='🇷🇺 Russian', callback_data='ru')
    uz = InlineKeyboardButton(text='🇺🇿 Uzbek', callback_data='uz')
    return InlineKeyboardMarkup(inline_keyboard=[[en], [ru], [uz]])

def cancel(id, lang):
    txt = get_text(lang,"cancel")
    button = InlineKeyboardButton(text=txt, callback_data=f"cancel_{id}")
    return InlineKeyboardMarkup(inline_keyboard=[[button]])

def phone_number_btn():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Telefon raqamni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )