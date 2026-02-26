import logging
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.api.client import backend_client
from src.keyboards.main_menu import get_main_menu_keyboard
from src.keyboards.swipe import get_swipe_keyboard, get_report_reason_keyboard
from src.utils.profile import _send_profile_album

router = Router()
logger = logging.getLogger(__name__)


class SwipeStates(StatesGroup):
    viewing_profile = State()
    reporting = State()


def _format_profile_text(profile: dict) -> str:
    user_name = profile.get('name') or profile.get('first_name') or 'Аноним'
    desc_parts = profile.get('description', '').split('\n\n🏋️ Опыт тренировок:')
    main_desc = desc_parts[0]
    experience = desc_parts[1] if len(desc_parts) > 1 else None
    
    text = (
        f"👤 <b>{user_name}</b>, {profile.get('age', '?')} лет\n\n"
        f"{main_desc}\n\n"
    )
    if experience:
        text += f"🏋️ <b>Опыт:</b> {experience}\n\n"
    return text.strip()


@router.message(F.text == "🔍 Начать свайпать")
async def start_swiping(message: types.Message, state: FSMContext):
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
        reply_markup=get_swipe_keyboard()
    )
    
    await show_next_profile(message, telegram_id, state)


async def show_next_profile(
    message: types.Message,
    telegram_id: int,
    state: FSMContext
):
    try:
        profile = await backend_client.get_next_profile(telegram_id)
    except Exception as e:
        logger.error(f"Error getting next profile: {e}")
        await message.answer("⚠️ Ошибка загрузки анкеты")
        return
    
    if not profile:
        await state.clear()
        await message.answer(
            "🎉 На сегодня всё!\nТы посмотрел все анкеты, зайди попозже.",
            reply_markup=get_main_menu_keyboard(has_profile=True)
        )
        return
    
    await state.update_data(current_profile_id=profile["user_id"])
    await state.set_state(SwipeStates.viewing_profile)
    
    text = _format_profile_text(profile)
    media_list = profile.get('media', [])
    
    await _send_profile_album(
        message=message,
        media_list=media_list,
        caption=text
    )


@router.message(F.text == "👍", StateFilter(SwipeStates.viewing_profile))
async def swipe_like(message: types.Message, state: FSMContext):
    await _process_swipe_action(message, state, "like")


@router.message(F.text == "👎", StateFilter(SwipeStates.viewing_profile))
async def swipe_dislike(message: types.Message, state: FSMContext):
    await _process_swipe_action(message, state, "dislike")


@router.message(F.text == "⚠️ Жалоба", StateFilter(SwipeStates.viewing_profile))
async def swipe_report_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    to_user_id = data.get("current_profile_id")
    
    if not to_user_id:
        await message.answer("⚠️ Ошибка: анкета не найдена")
        return
    
    await state.set_state(SwipeStates.reporting)
    await message.answer(
        "Выберите причину жалобы:",
        reply_markup=get_report_reason_keyboard(to_user_id)
    )


@router.callback_query(F.data.startswith("report_reason_"), StateFilter(SwipeStates.reporting))
async def swipe_report_submit(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    reason_key = parts[2]
    to_user_id = int(parts[3])
    telegram_id = callback.from_user.id
    
    reason_labels = {"spam": "Спам/реклама", "fake": "Фейковая анкета", "other": "Другое"}
    reason_text = reason_labels.get(reason_key, reason_key)
    
    try:
        await backend_client.send_action(
            telegram_id, to_user_id, "report", report_reason=reason_text
        )
    except Exception as e:
        logger.error(f"Error sending report: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)
        return
    
    await callback.message.answer("✅ Жалоба отправлена!")
    await state.clear()
    
    profile = await backend_client.get_profile(telegram_id)
    if profile:
        await show_next_profile(callback.message, telegram_id, state)


@router.callback_query(F.data == "cancel_report", StateFilter(SwipeStates.reporting))
async def cancel_report(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("✅ Отменено.")
    telegram_id = callback.from_user.id
    profile = await backend_client.get_profile(telegram_id)
    if profile:
        await show_next_profile(callback.message, telegram_id, state)


async def _process_swipe_action(
    message: types.Message,
    state: FSMContext,
    action_type: str
):
    telegram_id = message.from_user.id
    data = await state.get_data()
    to_user_id = data.get("current_profile_id")
    
    if not to_user_id:
        await message.answer("⚠️ Ошибка: анкета не найдена")
        return
    
    try:
        await backend_client.send_action(
            telegram_id=telegram_id,
            to_user_id=to_user_id,
            action_type=action_type
        )
    except Exception as e:
        logger.error(f"Error sending {action_type}: {e}")
        await message.answer("⚠️ Ошибка сети")
        return
        
    await show_next_profile(message, telegram_id, state)


async def start_swiping_callback(
    message: types.Message,
    telegram_id: int,
    state: FSMContext
):
    profile = await backend_client.get_profile(telegram_id)
    if not profile:
        await message.answer(
            "⚠️ Сначала создайте анкету!",
            reply_markup=get_main_menu_keyboard(has_profile=False)
        )
        return
    
    await message.answer(
        "🔍 Загружаю анкеты...\n\nИспользуй кнопки внизу:",
        reply_markup=get_swipe_keyboard()
    )
    
    await show_next_profile(message, telegram_id, state)