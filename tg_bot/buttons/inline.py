from aiofiles.os import access

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async

from tg_bot.buttons.text import ortga


def choose_language():
    en = InlineKeyboardButton(text='🇬🇧 English', callback_data='en')
    ru = InlineKeyboardButton(text='🇷🇺 Russian', callback_data='ru')
    uz = InlineKeyboardButton(text='🇺🇿 Uzbek', callback_data='uz')
    return InlineKeyboardMarkup(inline_keyboard=[[en], [ru], [uz]])

