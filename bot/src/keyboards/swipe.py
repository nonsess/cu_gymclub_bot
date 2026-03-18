from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_swipe_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👎"),
                KeyboardButton(text="👍"),
                KeyboardButton(text="⚠️ Жалоба"),
                KeyboardButton(text="💤"),
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие 👇"
    )


def get_report_reason_keyboard(action_id: int, user_id: int = None) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📢 Спам/реклама", callback_data=f"report_reason_spam_{action_id}")],
        [InlineKeyboardButton(text="👤 Фейковая анкета", callback_data=f"report_reason_fake_{action_id}")],
        [InlineKeyboardButton(text="⚠️ Другое", callback_data=f"report_reason_other_{action_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_report")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)