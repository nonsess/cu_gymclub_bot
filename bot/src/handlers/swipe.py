import logging
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.keyboards.profile import get_start_keyboard
from src.keyboards.swipe import get_swipe_keyboard, get_report_reason_keyboard
from src.api.client import backend_client

router = Router()
logger = logging.getLogger(__name__)


class SwipeStates(StatesGroup):
    viewing_profile = State()


@router.callback_query(F.data == "start_swiping")
async def start_swiping(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    
    profile = await backend_client.get_profile(telegram_id)
    if not profile:
        await callback.answer("Сначала создайте анкету!", show_alert=True)
        return
    
    await state.update_data(seen_ids=[])
    await show_next_profile(callback, telegram_id, seen_ids=[], state=state)


async def show_next_profile(
    callback: types.CallbackQuery | types.Message,
    telegram_id: int,
    seen_ids: list[int],
    state: FSMContext
):
    try:
        profile = await backend_client.get_next_profile(telegram_id, seen_ids)
    except Exception as e:
        logger.error(f"Error getting next profile: {e}")
        await callback.answer("⚠️ Ошибка загрузки анкеты", show_alert=True)
        return
    
    if not profile:
        await callback.message.edit_text(
            "🎉 На сегодня всё!\nЗавтра будут новые анкеты. Заходи позже!\n\n"
            "Или проверь раздел «Входящие лайки» ❤️",
            reply_markup=get_start_keyboard(has_profile=True)
        )
        return
    
    await state.update_data(
        current_profile_id=profile["id"],
        seen_ids=seen_ids + [profile["id"]]
    )
    
    await state.set_state(SwipeStates.viewing_profile)
    
    desc_parts = profile.get('description', '').split('\n\n🏋️ Опыт тренировок:')
    main_desc = desc_parts[0]
    experience = desc_parts[1] if len(desc_parts) > 1 else None
    
    text = (
        f"👤 <b>{profile.get('name', 'Аноним')}</b>, {profile.get('age', '?')} лет\n\n"
        f"{main_desc}\n\n"
        f"{f'🏋️ <b>Опыт:</b> {experience}' if experience else ''}"
    )
    
    if profile.get('photo_ids') and profile['photo_ids']:
        try:
            await callback.message.edit_media(
                media=types.InputMediaPhoto(media=profile['photo_ids'][0], caption=text, parse_mode="HTML"),
                reply_markup=get_swipe_keyboard()
            )
        except Exception:
            await callback.message.answer(text, reply_markup=get_swipe_keyboard(), parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=get_swipe_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "swipe_like", StateFilter(SwipeStates.viewing_profile))
async def swipe_like(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    data = await state.get_data()
    to_user_id = data.get("current_profile_id")
    seen_ids = data.get("seen_ids", [])
    
    if not to_user_id:
        await callback.answer("Ошибка: анкета не найдена", show_alert=True)
        return
    
    try:
        result = await backend_client.send_action(telegram_id, to_user_id, "like")
    except Exception as e:
        logger.error(f"Error sending like: {e}")
        await callback.answer("⚠️ Ошибка отправки лайка", show_alert=True)
        return
    
    if result.get("is_match"):
        await show_next_profile(callback, telegram_id, seen_ids, state)
    else:
        await show_next_profile(callback, telegram_id, seen_ids, state)


@router.callback_query(F.data == "swipe_dislike", StateFilter(SwipeStates.viewing_profile))
async def swipe_dislike(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    data = await state.get_data()
    to_user_id = data.get("current_profile_id")
    seen_ids = data.get("seen_ids", [])
    
    if to_user_id:
        try:
            await backend_client.send_action(telegram_id, to_user_id, "dislike")
        except Exception:
            pass
    
    await show_next_profile(callback, telegram_id, seen_ids, state)


@router.callback_query(F.data == "swipe_report", StateFilter(SwipeStates.viewing_profile))
async def swipe_report_start(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    to_user_id = data.get("current_profile_id")
    
    if not to_user_id:
        await callback.answer("Ошибка: анкета не найдена", show_alert=True)
        return
    
    await callback.message.edit_text(
        "⚠️ <b>Пожаловаться на пользователя</b>\n\n"
        "Выберите причину жалобы:",
        reply_markup=get_report_reason_keyboard(to_user_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("report_reason_"), StateFilter(SwipeStates.viewing_profile))
async def swipe_report_submit(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    reason = parts[2]
    to_user_id = parts[3]
    
    telegram_id = callback.from_user.id
    data = await state.get_data()
    seen_ids = data.get("seen_ids", [])
    
    reason_labels = {
        "spam": "Спам/реклама",
        "fake": "Фейковая анкета",
        "other": "Другое"
    }
    
    try:
        await backend_client.send_action(
            telegram_id, 
            int(to_user_id), 
            "report", 
            report_reason=reason_labels.get(reason, reason)
        )
    except Exception as e:
        logger.error(f"Error sending report: {e}")
        await callback.answer("⚠️ Ошибка отправки жалобы", show_alert=True)
        return
    
    await callback.message.edit_text(
        "✅ <b>Жалоба отправлена</b>\n\n"
        "Мы проверим эту анкету. Спасибо за бдительность!",
        parse_mode="HTML"
    )
    
    await show_next_profile(callback, telegram_id, seen_ids, state)