from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.api.client import backend_client
from src.keyboards.swipe import get_swipe_keyboard

router = Router()


class SwipeStates(StatesGroup):
    viewing_profile = State()
    deciding_on_incoming = State()


@router.callback_query(F.data == "start_swiping")
async def start_swiping(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    
    profile = await backend_client.get_profile(telegram_id)
    if not profile:
        await callback.answer("Сначала создайте анкету!", show_alert=True)
        return
    
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
        await callback.answer("⚠️ Ошибка загрузки анкеты", show_alert=True)
        return
    
    if not profile:
        await callback.message.edit_text(
            "🎉 На сегодня всё!\nЗавтра будут новые анкеты. Заходи позже!"
        )
        return
    
    await state.update_data(current_profile_id=profile["id"], seen_ids=seen_ids + [profile["id"]])
    
    text = (
        f"👤 <b>{profile.get('first_name', 'Аноним')}</b>, {profile['age']} лет\n\n"
        f"{profile['description']}\n\n"
        f"{'🏷 Интересы: ' + ', '.join(profile.get('interests', [])) if profile.get('interests') else ''}"
    )
    
    if profile.get('photo_ids') and profile['photo_ids']:
        await callback.message.edit_media(
            media=types.InputMediaPhoto(media=profile['photo_ids'][0], caption=text, parse_mode="HTML"),
            reply_markup=get_swipe_keyboard()
        )
    else:
        await callback.message.edit_text(text, reply_markup=get_swipe_keyboard(), parse_mode="HTML")
    
    await state.set_state(SwipeStates.viewing_profile)


@router.callback_query(F.data == "swipe_like", StateFilter(SwipeStates.viewing_profile))
async def swipe_like(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    data = await state.get_data()
    to_user_id = data.get("current_profile_id")
    
    if not to_user_id:
        await callback.answer("Ошибка: анкета не найдена", show_alert=True)
        return
    
    try:
        result = await backend_client.send_action(telegram_id, to_user_id, "like")
    except Exception:
        await callback.answer("⚠️ Ошибка отправки лайка", show_alert=True)
        return
    
    if result.get("is_match"):
        await callback.message.edit_text("🎉 <b>Это взаимно!</b>\n\nПроверьте раздел «Матчи»", parse_mode="HTML")
    else:
        await show_next_profile(callback, telegram_id, data.get("seen_ids", []), state)
    
    await state.clear()


@router.callback_query(F.data == "swipe_dislike", StateFilter(SwipeStates.viewing_profile))
async def swipe_dislike(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    data = await state.get_data()
    to_user_id = data.get("current_profile_id")
    
    if to_user_id:
        await backend_client.send_action(telegram_id, to_user_id, "dislike")
    
    await show_next_profile(callback, telegram_id, data.get("seen_ids", []), state)
    await state.clear()