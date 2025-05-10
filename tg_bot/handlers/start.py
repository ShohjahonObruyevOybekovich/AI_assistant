import os

from aiogram import Bot, F, types
from aiogram.fsm.context import FSMContext
from aiogram.handlers import CallbackQueryHandler
from aiogram.types import Message, BufferedInputFile, CallbackQuery
from icecream import ic

from account.models import CustomUser
from dispatcher import dp, TOKEN
from tg_bot.buttons.inline import choose_language, cancel
from tg_bot.handlers.finance import FinanceHandler
from tg_bot.state.main import User
from tg_bot.utils.ai import GptFunctions
from tg_bot.utils.stt import stt
from tg_bot.utils.translator import get_text, load_locales

bot = Bot(token=TOKEN)
gpt = GptFunctions()
load_locales()


# /start handler
@dp.message(F.text == "/start")
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()

    user = CustomUser.objects.filter(chat_id=message.from_user.id).first()
    lang = getattr(user, 'language', 'uz')

    # First-time user registration
    if not user:
        CustomUser.objects.create(
            chat_id=message.from_user.id,
            full_name=message.from_user.full_name,
        )
        await message.answer(get_text(lang, "start_message"), reply_markup=choose_language())
        await state.set_state(User.lang)
        return

    # Blocked user
    if user.is_blocked:
        await message.answer(get_text(lang, "is_blocked"), reply_markup=choose_language())
        return

    # Admin specific logic can go here
    if user.role == "ADMIN":
        # Optional: send admin-specific buttons or info
        pass
    if user:
        await message.answer(get_text(lang, "say_something_to_start"))


@dp.callback_query(lambda call: call.data in ["uz" , "ru" , "en"])
async def user_lang_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)

    selected_lang = call.data.strip().lower()
    user = CustomUser.objects.filter(chat_id=call.from_user.id).first()

    if user:
        user.language = selected_lang
        user.save()
        await call.message.reply(get_text(selected_lang, "language_selected"))
        await call.message.answer(get_text(selected_lang, "say_something_to_start"))

    await state.clear()


# Voice message handler
@dp.message(F.content_type == types.ContentType.VOICE)
async def handle_voice(message: Message, bot: Bot):
    file = await bot.get_file(message.voice.file_id)
    file_path = f"voice_{message.from_user.id}.ogg"
    destination_path = file_path.replace(".ogg", ".mp3")
    ic(file_path)

    file_bytes = await bot.download_file(file.file_path)
    with open(file_path, "wb") as f:
        f.write(file_bytes.read())

    os.system(f"ffmpeg -i {file_path} -ar 16000 -ac 1 {destination_path}")

    if not os.path.exists(destination_path):
        await message.answer("❌ Failed to convert audio.")
        return

    result = stt(destination_path)
    text = result.get("result", {}).get("text") if isinstance(result, dict) else result

    lang = CustomUser.objects.filter(chat_id=message.from_user.id).first()

    await message.reply(
        text=f"{get_text(lang, "message")} : {text}",
        reply_markup=cancel(lang=lang,id=message.from_user.id),
    )

    if text:
        intent_result = await gpt.prompt_to_json(str(message.from_user.id), text)
        ic(intent_result)

        action_type = intent_result.get("action", "")
        ic(action_type)

        actions = [
            "create_income",
            "create_expense",
            "edit_finance",
            "list_finance",
            "excel_data",
            "dollar_course"
        ]

        if not action_type:
            await message.reply(get_text(lang, "unknown_command"))

        elif action_type in actions:
            finance = FinanceHandler(user_id=message.from_user.id)
            result = await finance.route(intent_result)

            if isinstance(result, BufferedInputFile):
                await message.answer_document(result, caption="📊 Hisobot tayyor!")
            else:
                await message.answer(result)

        else:
            await message.reply(get_text(lang, "unsupported_action"))
    # Cleanup
    os.remove(file_path)
    os.remove(destination_path)
