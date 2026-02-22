from aiogram import Router, F, types
from aiogram.filters import Command
from src.api.client import backend_client
from src.keyboards.profile import get_start_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    try:
        await backend_client.register_user(telegram_id, username, first_name)
    except Exception as e:
        await message.answer("⚠️ Ошибка регистрации. Попробуйте позже.")
        return
    
    try:
        profile = await backend_client.get_profile(telegram_id)
    except Exception:
        profile = None
    
    if profile:
        await message.answer(
            f"👋 Привет, {first_name}!\n\n"
            f"У вас уже есть анкета. Хотите редактировать или начать свайпать?",
            reply_markup=get_start_keyboard(has_profile=True)
        )
    else:
        await message.answer(
            f"👋 Привет, {first_name}!\n\n"
            f"Давай создадим анкету, чтобы найти тренировочного партнёра 💪",
            reply_markup=get_start_keyboard(has_profile=False)
        )