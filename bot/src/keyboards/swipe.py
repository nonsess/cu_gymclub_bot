from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_swipe_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Дизлайк", callback_data="swipe_dislike"),
            InlineKeyboardButton(text="❤️ Лайк", callback_data="swipe_like"),
        ],
        [
            InlineKeyboardButton(text="⚠️ Пожаловаться", callback_data="swipe_report"),
        ]
    ])


def get_report_reason_keyboard(to_user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Спам/реклама", callback_data=f"report_reason_spam_{to_user_id}")],
        [InlineKeyboardButton(text="🎭 Фейковая анкета", callback_data=f"report_reason_fake_{to_user_id}")],
        [InlineKeyboardButton(text="📝 Другое", callback_data=f"report_reason_other_{to_user_id}")],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="swipe_dislike")],
    ])


def get_decide_keyboard(target_user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️ Взаимно", callback_data=f"decide_like_{target_user_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"decide_dislike_{target_user_id}"),
        ]
    ])


def get_match_keyboard(telegram_username: str) -> InlineKeyboardMarkup:
    link = f"https://t.me/{telegram_username}" if telegram_username else None
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Написать", url=link)] if link else []
    ])