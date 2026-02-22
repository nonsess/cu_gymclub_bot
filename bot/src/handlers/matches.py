from aiogram import Router, F, types
from src.api.client import backend_client
from src.keyboards.swipe import get_decide_keyboard, get_match_keyboard

router = Router()


@router.callback_query(F.data == "check_incoming")
async def check_incoming(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id
    
    try:
        incoming = await backend_client.get_incoming_likes(telegram_id)
    except Exception:
        await callback.answer("⚠️ Ошибка загрузки", show_alert=True)
        return
    
    if not incoming:
        await callback.answer("Пока нет новых лайков ❤️", show_alert=True)
        return
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(
            text=f"👤 Анкета #{like['from_user_id']}",
            callback_data=f"reveal_{like['from_user_id']}"
        )]
        for like in incoming
    ])
    
    await callback.message.edit_text(
        f"❤️ У вас {len(incoming)} новых лайков!\nВыберите анкету:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("reveal_"))
async def reveal_profile(callback: types.CallbackQuery):
    from_user_id = int(callback.data.split("_")[1])
    telegram_id = callback.from_user.id
    
    keyboard = get_decide_keyboard(from_user_id)
    
    await callback.message.edit_text(
        f"👤 Анкета пользователя #{from_user_id}\n\n"
        f"Что делаем?",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("decide_"))
async def decide_on_incoming(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    action_type = parts[1]
    target_user_id = int(parts[2])
    telegram_id = callback.from_user.id
    
    try:
        result = await backend_client.decide_on_incoming(telegram_id, target_user_id, action_type)
    except Exception:
        await callback.answer("⚠️ Ошибка", show_alert=True)
        return
    
    if result.get("is_match"):
        matches = await backend_client.get_matches(telegram_id)
        matched = next((m for m in matches if m["user1_id"] == target_user_id or m["user2_id"] == target_user_id), None)
        
        if matched:
            keyboard = get_match_keyboard(None)  # TODO: получить username
            await callback.message.edit_text(
                "🎉 <b>Матч!</b>\n\nВы понравились друг другу.",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    else:
        await callback.message.edit_text("✅ Решение сохранено")
    
    await callback.answer()