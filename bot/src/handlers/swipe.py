import logging
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.api.client import backend_client
from src.keyboards.main_menu import get_main_menu_keyboard, hide_keyboard
from src.keyboards.swipe import get_swipe_keyboard, get_report_reason_keyboard

router = Router()
logger = logging.getLogger(__name__)

class SwipeStates(StatesGroup):
    viewing_profile = State()

async def _send_profile_update(
    target: types.CallbackQuery | types.Message,
    text: str,
    photo_id: str | None,
    reply_markup,
    parse_mode: str = "HTML"
):
    is_callback = isinstance(target, types.CallbackQuery)
    
    try:
        if photo_id:
            if is_callback:
                try:
                    await target.message.edit_media(
                        media=types.InputMediaPhoto(media=photo_id, caption=text, parse_mode=parse_mode),
                        reply_markup=reply_markup
                    )
                    return
                except Exception as e:
                    logger.debug(f"edit_media failed, falling back to answer_photo: {e}")
                await target.message.answer_photo(
                    photo=photo_id,
                    caption=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup
                )
            else:
                await target.answer_photo(
                    photo=photo_id,
                    caption=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup
                )
        else:
            if is_callback:
                try:
                    await target.message.edit_text(
                        text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
                    return
                except Exception as e:
                    logger.debug(f"edit_text failed, falling back to answer: {e}")
                await target.message.answer(
                    text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            else:
                await target.answer(
                    text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
    except Exception as e:
        logger.error(f"Error sending profile update: {e}")
        if is_callback:
            await target.answer("⚠️ Ошибка отображения", show_alert=True)
        else:
            await target.answer("⚠️ Ошибка отображения")


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


@router.callback_query(F.data == "start_swiping")
async def start_swiping(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    
    profile = await backend_client.get_profile(telegram_id)
    if not profile:
        await callback.answer("⚠️ Сначала создайте анкету!", show_alert=True)
        return
    
    await show_next_profile(callback, telegram_id, state=state)


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
    
    await show_next_profile(message, telegram_id, state=state)


async def show_next_profile(
    callback: types.CallbackQuery | types.Message,
    telegram_id: int,
    state: FSMContext
):
    try:
        profile = await backend_client.get_next_profile(telegram_id)
    except Exception as e:
        logger.error(f"Error getting next profile for user {telegram_id}: {e}")
        
        error_text = "⚠️ Ошибка загрузки анкеты. Попробуйте позже."
        if isinstance(callback, types.CallbackQuery):
            await callback.answer(error_text, show_alert=True)
        else:
            await callback.answer(error_text)
        return
    
    if not profile:
        text = (
            "🎉 На сегодня всё!\n\n"
            "Завтра будут новые анкеты. Заходи позже!\n\n"
            "Или проверь раздел «❤️ Входящие лайки»"
        )
        
        await callback.message.answer(
            text,
            reply_markup=get_main_menu_keyboard(has_profile=True)
        )
        
        try:
            await callback.message.delete()
        except Exception as e:
            logger.debug(f"Failed to delete old message: {e}")
        
        await state.clear()
        return
    
    await state.update_data(current_profile_id=profile["id"])
    await state.set_state(SwipeStates.viewing_profile)
    
    text = _format_profile_text(profile)
    photo_id = profile['photo_ids'][0] if profile.get('photo_ids') else None
    
    await _send_profile_update(
        target=callback,
        text=text,
        photo_id=photo_id,
        reply_markup=get_swipe_keyboard()
    )


async def _process_swipe_action(
    callback: types.CallbackQuery,
    state: FSMContext,
    action_type: str,
    success_message: str | None = None
):
    telegram_id = callback.from_user.id
    data = await state.get_data()
    to_user_id = data.get("current_profile_id")
    
    if not to_user_id:
        await callback.answer("⚠️ Ошибка: анкета не найдена", show_alert=True)
        return
    
    try:
        result = await backend_client.send_action(telegram_id, to_user_id, action_type)
    except Exception as e:
        logger.error(f"Error sending {action_type} action: {e}")
        await callback.answer(f"⚠️ Ошибка отправки {action_type}", show_alert=True)
        return
    
    if result.get("is_match") and action_type == "like":
        logger.info(f"🎉 Match! User {telegram_id} matched with {to_user_id}")
    
    if success_message:
        await callback.answer(success_message)
    
    await show_next_profile(callback, telegram_id, state)


@router.callback_query(F.data == "swipe_like", StateFilter(SwipeStates.viewing_profile))
async def swipe_like(callback: types.CallbackQuery, state: FSMContext):
    await _process_swipe_action(callback, state, action_type="like")


@router.callback_query(F.data == "swipe_dislike", StateFilter(SwipeStates.viewing_profile))
async def swipe_dislike(callback: types.CallbackQuery, state: FSMContext):
    await _process_swipe_action(callback, state, action_type="dislike")


@router.callback_query(F.data == "swipe_report", StateFilter(SwipeStates.viewing_profile))
async def swipe_report_start(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    to_user_id = data.get("current_profile_id")
    
    if not to_user_id:
        await callback.answer("⚠️ Ошибка: анкета не найдена", show_alert=True)
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
    reason_key = parts[2]
    to_user_id = int(parts[3])
    telegram_id = callback.from_user.id
    
    reason_labels = {
        "spam": "Спам/реклама",
        "fake": "Фейковая анкета",
        "other": "Другое"
    }
    reason_text = reason_labels.get(reason_key, reason_key)
    
    try:
        await backend_client.send_action(
            telegram_id,
            to_user_id,
            "report",
            report_reason=reason_text
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
    
    await show_next_profile(callback, telegram_id, state)