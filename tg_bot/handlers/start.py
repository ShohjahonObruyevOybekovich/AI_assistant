import os

from aiogram import types, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from icecream import ic

from account.models import CustomUser
from dispatcher import dp , TOKEN
from tg_bot.buttons.inline import choose_language
from tg_bot.state.main import *
from tg_bot.utils.ai import  extract_intent_and_handle
from tg_bot.utils.stt import stt
from tg_bot.utils.translator import get_text, load_locales

bot = Bot(token=TOKEN)
load_locales()
@dp.message(lambda msg: msg.text == "/start")
async def command_start_handler(message: Message, state: FSMContext) -> None:

    await state.clear()
    user = CustomUser.objects.filter(chat_id=message.from_user.id).first()
    lang = getattr(user, 'language', 'uz')

    if not user:
        CustomUser.objects.create(chat_id=message.from_user.id, language=lang, full_name=message.from_user.full_name)
        await message.answer(
            text=get_text(lang, "start_message"),
            reply_markup=choose_language()
        )
        await state.set_state(User.lang)

    if user and user.role == "ADMIN" and not user.is_blocked:
        # await message.answer()
        pass


    if user and user.is_blocked:
        await message.answer(
            text=get_text(lang, "is_blocked"),
            reply_markup=choose_language()
        )

    await message.answer(
        text=get_text(lang, "start_message"),
    )
    await message.answer(
        text=get_text(lang, "say_something_to_start"),
    )



@dp.message(User.lang)
async def user_lang_handler(message: Message, state: FSMContext) :
    data = await state.get_data()
    data["lang"] = message.text
    await state.update_data(data)
    user = CustomUser.objects.filter(chat_id=message.from_user.id).first()

    if user :
        user.language = data["lang"]
        user.save()
        lang = getattr(user, 'language', 'uz')
        await message.reply(
            text=get_text(lang,"language_selected")
        )
        await message.answer(
            text=get_text(lang, "say_something_to_start"),
        )
    await state.clear()



@dp.message(F.content_type == types.ContentType.VOICE)
async def handle_voice(message: types.Message, bot: Bot):
    file = await bot.get_file(message.voice.file_id)
    file_path = f"voice_{message.from_user.id}.ogg"
    destination_path = file_path.replace(".ogg", ".mp3")
    ic(file_path)

    file_bytes = await bot.download_file(file.file_path)
    with open(file_path, "wb") as f:
        f.write(file_bytes.read())

    os.system(f"ffmpeg -i {file_path} -ar 16000 -ac 1 {destination_path}")

    if not os.path.exists(destination_path):
        await message.answer("\u274c Failed to convert audio.")
        return

    result = stt(destination_path)
    text = result.get("result", {}).get("text") if isinstance(result, dict) else result

    await message.reply(f"🔊 Transcribed: {text}")

    if text:
        intent_result = extract_intent_and_handle(text, str(message.from_user.id))
        if "error" in intent_result:
            await message.reply(f"⚠️ {intent_result['error']}")
        else:
            action_type = intent_result.get("action_type", "query")
            logs = intent_result.get("logs")
            if logs:
                response = f"✅ Action Type: {action_type}\n" + "\n".join(logs)
            else:
                response = f"✅ Action Type: {action_type}\n" + "\n".join(f"{k}: {v}" for k, v in intent_result.items() if k != "action_type")
            await message.reply(response)

    os.remove(file_path)
    os.remove(destination_path)

