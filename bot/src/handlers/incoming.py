import logging
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.utils.profile import _send_profile_album
from src.keyboards.main_menu import get_main_menu_keyboard
from src.keyboards.swipe import get_swipe_keyboard, get_report_reason_keyboard
from src.api.client import backend_client

router = Router()
logger = logging.getLogger(__name__)


class IncomingStates(StatesGroup):
    viewing_incoming = State()
    reporting = State()


@router.callback_query(F.data == "check_incoming")
async def check_incoming(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    await state.update_data(seen_ids=[])
    
    await callback.message.answer(
        "🔍 Загружаю входящие лайки...\n\nИспользуй кнопки внизу:",
        reply_markup=get_swipe_keyboard()
    )
    
    await show_next_incoming(callback.message, telegram_id, state)


async def show_next_incoming(
    message: types.Message,
    telegram_id: int,
    state: FSMContext
):
    try:
        profile = await backend_client.get_next_incoming_like(telegram_id)
    except Exception as e:
        logger.error(f"Error getting next incoming like: {e}")
        profile = None
    
    if not profile:
        await state.clear()
        await message.answer(
            "🎉 Вы посмотрели все входящие лайки!\nЗаходите позже ❤️",
            reply_markup=get_main_menu_keyboard(has_profile=True)
        )
        return

    await state.update_data(current_incoming_id=profile["id"])
    await state.set_state(IncomingStates.viewing_incoming)
    
    desc_parts = profile.get('description', '').split('\n\n🏋️ Опыт тренировок:')
    main_desc = desc_parts[0]
    experience = desc_parts[1] if len(desc_parts) > 1 else None
    
    text = (
        f"👤 <b>{profile.get('name', 'Аноним')}</b>, {profile.get('age', '?')} лет\n\n"
        f"{main_desc}\n\n"
        f"{f'🏋️ <b>Опыт:</b> {experience}' if experience else ''}\n\n"
        f"<i>Ответьте взаимностью или пропустите</i>"
    )
    
    media_ids = profile.get('photo_ids', [])
    await _send_profile_album(message, media_ids, text)


@router.message(F.text == "👍", StateFilter(IncomingStates.viewing_incoming))
async def incoming_like(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    data = await state.get_data()
    to_user_id = data.get("current_incoming_id")
    
    if not to_user_id:
        await message.answer("⚠️ Ошибка: анкета не найдена")
        return
    
    try:
        await backend_client.decide_on_incoming(telegram_id, to_user_id, "like")
    except Exception as e:
        logger.error(f"Error: {e}")
        await message.answer("⚠️ Ошибка")
        return
    
    await show_next_incoming(message, telegram_id, state)


@router.message(F.text == "👎", StateFilter(IncomingStates.viewing_incoming))
async def incoming_dislike(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    data = await state.get_data()
    to_user_id = data.get("current_incoming_id")
    
    if to_user_id:
        try:
            await backend_client.decide_on_incoming(telegram_id, to_user_id, "dislike")
        except:
            pass
    
    await show_next_incoming(message, telegram_id, state)


@router.message(F.text == "⚠️ Жалоба", StateFilter(IncomingStates.viewing_incoming))
async def incoming_report_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    to_user_id = data.get("current_incoming_id")
    
    if not to_user_id:
        await message.answer("⚠️ Ошибка: анкета не найдена")
        return
    
    await state.set_state(IncomingStates.reporting)
    await message.answer(
        "Выберите причину жалобы:",
        reply_markup=get_report_reason_keyboard(to_user_id)
    )


@router.callback_query(F.data.startswith("report_reason_"), StateFilter(IncomingStates.reporting))
async def incoming_report_submit(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    reason = parts[2]
    to_user_id = int(parts[3])
    telegram_id = callback.from_user.id
    
    reason_labels = {"spam": "Спам/реклама", "fake": "Фейковая анкета", "other": "Другое"}
    
    try:
        await backend_client.send_action(
            telegram_id, to_user_id, "report", report_reason=reason_labels.get(reason, reason)
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)
        return
    
    await callback.message.answer("✅ Жалоба отправлена!")
    await state.clear()
    
    telegram_id = callback.from_user.id
    await show_next_incoming(callback.message, telegram_id, state)


@router.callback_query(F.data == "cancel_report", StateFilter(IncomingStates.reporting))
async def cancel_report(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("✅ Отменено.")
    await show_next_incoming(callback.message, callback.from_user.id, state)


async def check_incoming_from_menu(
    message: types.Message,
    telegram_id: int,
    state: FSMContext
):
    await state.clear()
    await state.update_data(seen_ids=[])
    
    await message.answer(
        "🔍 Загружаю входящие лайки...\n\nИспользуй кнопки внизу:",
        reply_markup=get_swipe_keyboard()
    )
    await show_next_incoming(message, telegram_id, state)