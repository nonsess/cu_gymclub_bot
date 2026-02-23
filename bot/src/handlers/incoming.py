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


class IncomingStates(StatesGroup):
    viewing_incoming = State()


@router.callback_query(F.data == "check_incoming")
async def check_incoming(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    
    await state.update_data(seen_ids=[])
    await show_next_incoming(callback, telegram_id, seen_ids=[], state=state)


async def show_next_incoming(
    callback: types.CallbackQuery | types.Message,
    telegram_id: int,
    seen_ids: list[int],
    state: FSMContext
):
    try:
        profile = await backend_client.get_next_incoming_like(telegram_id, seen_ids)
    except Exception as e:
        logger.error(f"Error getting next incoming like: {e}")
        profile = None
    
    if not profile:
        await callback.message.edit_text(
            "🎉 Вы посмотрели все входящие лайки!\n\n"
            "Заходите позже — возможно, появятся новые ❤️",
            reply_markup=get_start_keyboard(has_profile=True)
        )
        await state.clear()
        return
    
    await state.update_data(
        current_incoming_id=profile["id"],
        incoming_seen_ids=seen_ids + [profile["id"]]
    )
    
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


@router.callback_query(F.data == "swipe_like", StateFilter(IncomingStates.viewing_incoming))
async def incoming_like(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    data = await state.get_data()
    to_user_id = data.get("current_incoming_id")
    seen_ids = data.get("incoming_seen_ids", [])
    
    if not to_user_id:
        await callback.answer("Ошибка: анкета не найдена", show_alert=True)
        return
    
    try:
        result = await backend_client.decide_on_incoming(telegram_id, to_user_id, "like")
    except Exception as e:
        logger.error(f"Error sending incoming like: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)
        return
    
    if result.get("is_match"):
        await callback.message.edit_text(
            "🎉 <b>Это взаимно!</b>\n\n"
            f"Вы понравились друг другу.\n\n"
            "Теперь вы можете написать друг другу! 💌",
            parse_mode="HTML"
        )
    else:
        await callback.answer("✅ Вы ответили взаимностью!")
    
    await show_next_incoming(callback, telegram_id, seen_ids, state)


@router.callback_query(F.data == "swipe_dislike", StateFilter(IncomingStates.viewing_incoming))
async def incoming_dislike(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    data = await state.get_data()
    to_user_id = data.get("current_incoming_id")
    seen_ids = data.get("incoming_seen_ids", [])
    
    if to_user_id:
        try:
            await backend_client.decide_on_incoming(telegram_id, to_user_id, "dislike")
        except Exception:
            pass
    
    await show_next_incoming(callback, telegram_id, seen_ids, state)


@router.callback_query(F.data == "swipe_report", StateFilter(IncomingStates.viewing_incoming))
async def incoming_report(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    to_user_id = data.get("current_incoming_id")
    
    if not to_user_id:
        await callback.answer("Ошибка: анкета не найдена", show_alert=True)
        return
    
    await callback.message.edit_text(
        "⚠️ <b>Пожаловаться на пользователя</b>\n\n"
        "Выберите причину:",
        reply_markup=get_report_reason_keyboard(to_user_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("report_reason_"), StateFilter(IncomingStates.viewing_incoming))
async def incoming_report_submit(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    reason = parts[2]
    to_user_id = parts[3]
    telegram_id = callback.from_user.id
    data = await state.get_data()
    seen_ids = data.get("incoming_seen_ids", [])
    
    reason_labels = {"spam": "Спам/реклама", "fake": "Фейковая анкета", "other": "Другое"}
    
    try:
        await backend_client.send_action(
            telegram_id, 
            int(to_user_id), 
            "report", 
            report_reason=reason_labels.get(reason, reason)
        )
    except Exception as e:
        logger.error(f"Error sending report: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=True)
        return
    
    await callback.message.edit_text(
        "✅ <b>Жалоба отправлена</b>\n\n"
        "Мы проверим эту анкету. Спасибо!",
        parse_mode="HTML"
    )
    
    await show_next_incoming(callback, telegram_id, seen_ids, state)