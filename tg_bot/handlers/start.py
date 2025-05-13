import os

from aiogram import Bot, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BufferedInputFile, CallbackQuery
from icecream import ic

from account.models import CustomUser
from dispatcher import dp, TOKEN
from tg_bot.buttons.inline import choose_language, cancel, phone_number_btn
from tg_bot.handlers.route import route_intent
from tg_bot.state.main import User
from tg_bot.test import format_phone_number
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


@dp.callback_query(lambda call: call.data in ["uz", "ru", "en"])
async def user_lang_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)

    selected_lang = call.data.strip().lower()
    user = CustomUser.objects.filter(chat_id=call.from_user.id).first()

    if user:
        user.language = selected_lang
        user.save()
        await call.message.answer(get_text(selected_lang, "language_selected"))
        await call.message.answer("📞 Iltimos, tugma orqali telefon raqam yuboring.", reply_markup=phone_number_btn())
        await state.set_state(User.phone)


@dp.message(User.phone)
async def handle_phone(message: Message, state: FSMContext):
    if message.contact:
        phone = message.contact.phone_number
        phone = format_phone_number(phone)
        ic(phone)
        existing_user = CustomUser.objects.filter(phone=phone).exclude(chat_id=message.from_user.id).first()

        if existing_user:
            await message.answer("❌ Bu telefon raqami boshqa foydalanuvchi tomonidan ishlatilmoqda.")
            return

        user = CustomUser.objects.filter(chat_id=message.from_user.id).first()
        user.phone = phone
        user.save()

        await message.answer("✅ Telefon raqamingiz muvaffaqiyatli saqlandi.")
        await state.clear()
        await message.answer(get_text(user.language, "say_something_to_start"))
    else:
        await message.answer("📞 Iltimos, tugma orqali telefon raqam yuboring.")
        await state.set_state(User.phone)



@dp.message(lambda msg: not msg.voice and msg.text and msg.text.isalnum())
async def ask_for_voice(msg:Message):
    await msg.answer("Menga ovozli xabar yuboring ...")


# Voice message handler

@dp.message(F.content_type == types.ContentType.VOICE)
async def handle_voice(message: Message, bot: Bot):
    # Save voice to file
    file = await bot.get_file(message.voice.file_id)
    file_path = f"voice_{message.from_user.id}.ogg"
    destination_path = file_path.replace(".ogg", ".mp3")
    ic(file_path)

    file_bytes = await bot.download_file(file.file_path)
    with open(file_path, "wb") as f:
        f.write(file_bytes.read())

    # Convert to MP3 using ffmpeg
    os.system(f"ffmpeg -i {file_path} -ar 16000 -ac 1 {destination_path}")

    if not os.path.exists(destination_path):
        await message.answer("❌ Failed to convert audio.")
        return

    # Transcribe audio
    result = stt(destination_path)
    text = result.get("result", {}).get("text") if isinstance(result, dict) else result

    lang_user = CustomUser.objects.filter(chat_id=message.from_user.id).first()

    await message.reply(
        text=f"{get_text(lang_user, 'message')} : {text}",
        reply_markup=cancel(lang=lang_user, id=message.from_user.id),
    )

    if not text:
        await message.reply(get_text(lang_user, "unknown_command"))
        return

    intent_result = await gpt.prompt_to_json(str(message.from_user.id), text)
    ic(intent_result)

    responses = []

    if isinstance(intent_result, list):
        for entry in intent_result:
            result = await route_intent(message.from_user.id, entry)
            if isinstance(result, BufferedInputFile):
                await message.answer_document(result, caption="📊 Hisobot tayyor!")
            elif result:
                responses.append(result)
    else:
        result = await route_intent(message.from_user.id, intent_result)
        if isinstance(result, BufferedInputFile):
            await message.answer_document(result, caption="📊 Hisobot tayyor!")
        elif result:
            responses.append(result)

    for chunk in responses:
        await message.answer(chunk)

    # Cleanup
    for path in [file_path, destination_path]:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass