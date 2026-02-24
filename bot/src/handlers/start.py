import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.api.client import backend_client
from src.keyboards.main_menu import get_main_menu_keyboard, hide_keyboard

router = Router()
logger = logging.getLogger(__name__)


async def show_main_menu(message: types.Message, telegram_id: int):
    try:
        profile = await backend_client.get_profile(telegram_id)
        has_profile = bool(profile)
    except Exception as e:
        logger.error(f"Error getting profile for menu: {e}")
        has_profile = False
    
    first_name = message.from_user.first_name or "Друг"
    
    if has_profile:
        text = (
            f"👋 Привет, {first_name}!\n\n"
            f"У вас уже есть анкета. Что делаем?"
        )
    else:
        text = (
            f"👋 Привет, {first_name}!\n\n"
            f"Давай создадим анкету, чтобы найти тренировочного партнёра 💪"
        )
    
    await message.answer(
        text,
        reply_markup=get_main_menu_keyboard(has_profile=has_profile)
    )

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    try:
        await backend_client.register_user(telegram_id, username, first_name)
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        await message.answer("⚠️ Ошибка регистрации. Попробуйте позже.")
        return
    
    await state.clear()
    
    await show_main_menu(message, telegram_id)


@router.message(F.text == "🔍 Начать свайпать")
async def on_start_swiping(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    
    profile = await backend_client.get_profile(telegram_id)
    if not profile:
        await message.answer(
            "⚠️ Сначала создайте анкету!",
            reply_markup=get_main_menu_keyboard(has_profile=False)
        )
        return
    
    await message.answer(
        "🔍 Загружаю анкеты...",
        reply_markup=hide_keyboard()
    )
    
    from src.handlers.swipe import start_swiping_callback
    await start_swiping_callback(message, telegram_id, state)


@router.message(F.text == "👤 Моя анкета")
async def on_my_profile(message: types.Message):
    telegram_id = message.from_user.id
    
    from src.handlers.profile import show_my_profile_message
    await show_my_profile_message(message, telegram_id)


@router.message(F.text == "❤️ Входящие лайки")
async def on_incoming_likes(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
        
    from src.handlers.incoming import check_incoming_from_menu
    await check_incoming_from_menu(message, telegram_id, state)

@router.message(F.text == "🔙 Назад")
async def on_back(message: types.Message, state: FSMContext):
    await state.clear()
    await show_main_menu(message, message.from_user.id)

@router.message(F.text == "📝 Создать анкету")
async def on_create_profile(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    
    await state.clear()
    
    from src.handlers.profile import start_create_profile_from_menu
    await start_create_profile_from_menu(message, telegram_id, state)