from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from tg_bot.buttons.text import *



def menu_btn():
    k2 = KeyboardButton(text = orders_list_txt)
    design = [
        [k2],
    ]
    return ReplyKeyboardMarkup(keyboard=design , resize_keyboard=True)

def phone_number_btn():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = "Raqamni yuborish 📞",
                                                         request_contact=True) ]] ,
                               resize_keyboard=True)


def back():
    keyboard1 = KeyboardButton(text = ortga)
    design = [[keyboard1]]
    return ReplyKeyboardMarkup(keyboard=design , resize_keyboard=True)
