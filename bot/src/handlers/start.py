import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup

from src.api.client import backend_client
from src.keyboards.main_menu import get_main_menu_keyboard
from src.keyboards.admin import get_admin_menu_keyboard
from src.utils.admin import is_admin

router = Router()
logger = logging.getLogger(__name__)

async def show_main_menu(message: types.Message, telegram_id: int):
    profile = await backend_client.get_profile(telegram_id)
    has_profile = bool(profile)
    
    is_admin_user = is_admin(telegram_id)
    
    first_name = message.from_user.first_name or "Друг"
    
    if has_profile:
        text = (
            f"👋 Привет, {first_name}!\n\n"
            f"У тебя уже есть анкета. Что делаем?"
        )
    else:
        text = (
            f"👋 Привет, {first_name}!\n\n"
            f"Давай создадим анкету, чтобы найти тренировочного партнёра 💪"
        )
    
    if is_admin_user:
        main_kb = get_main_menu_keyboard(has_profile=has_profile)
        admin_kb = get_admin_menu_keyboard()
        
        combined_buttons = main_kb.keyboard + admin_kb.keyboard
        
        await message.answer(
            text,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=combined_buttons,
                resize_keyboard=True,
                one_time_keyboard=False
            )
        )
    else:
        await message.answer(
            text,
            reply_markup=get_main_menu_keyboard(has_profile=has_profile)
        )


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    await backend_client.register_user(telegram_id, username, first_name)
    
    await state.clear()
    await show_main_menu(message, telegram_id)

@router.message(F.text == "🔍 Начать свайпать")
async def on_start_swiping(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    
    profile = await backend_client.get_profile(telegram_id)
    if not profile:
        await message.answer(
            "⚠️ Сначала создай анкету!",
            reply_markup=get_main_menu_keyboard(has_profile=False)
        )
        return
    
    from src.handlers.swipe import start_swiping_callback
    await start_swiping_callback(message, telegram_id, state)

@router.message(F.text == "👤 Моя анкета")
async def on_my_profile(message: types.Message):
    telegram_id = message.from_user.id

    profile = await backend_client.get_profile(telegram_id)
    if not profile:
        await message.answer(
            "⚠️ Сначала создай анкету!",
            reply_markup=get_main_menu_keyboard(has_profile=False)
        )
        return
    
    from src.handlers.profile import show_my_profile_message
    await show_my_profile_message(message, telegram_id)

@router.message(F.text == "❤️ Входящие лайки")
async def on_incoming_likes(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id

    profile = await backend_client.get_profile(telegram_id)
    if not profile:
        await message.answer(
            "⚠️ Сначала создай анкету!",
            reply_markup=get_main_menu_keyboard(has_profile=False)
        )
        return
        
    from src.handlers.incoming import check_incoming_from_menu
    await check_incoming_from_menu(message, telegram_id, state)

@router.message(F.text == "🔙 Назад")
async def on_back(message: types.Message, state: FSMContext):
    await state.clear()
    await show_main_menu(message, message.from_user.id)

@router.message(F.text == "📝 Создать анкету")
async def on_create_profile(message: types.Message, state: FSMContext):
    first_name = message.from_user.first_name
    
    await state.clear()
    
    from src.handlers.profile import start_create_profile_from_menu
    await start_create_profile_from_menu(message, first_name, state)