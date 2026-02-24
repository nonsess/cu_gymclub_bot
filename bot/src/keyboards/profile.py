from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_profile_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile"),
            InlineKeyboardButton(text="🗑 Удалить анкету", callback_data="delete_profile"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start"),
        ]
    ])


def get_edit_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Описание", callback_data="edit_description")],
        [InlineKeyboardButton(text="🎂 Возраст", callback_data="edit_age")],
        [InlineKeyboardButton(text="👤 Пол", callback_data="edit_gender")],
        [InlineKeyboardButton(text="💪 Опыт", callback_data="edit_experience")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="my_profile")],
    ])

def get_confirmation_keyboard(confirm_callback: str, cancel_callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=confirm_callback),
            InlineKeyboardButton(text="❌ Нет", callback_data=cancel_callback),
        ]
    ])


def get_inline_back_keyboard(callback_data: str = "back_to_start") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
    ])

def get_gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👨 Парень", callback_data="gender_male"),
            InlineKeyboardButton(text="👩 Девушка", callback_data="gender_female"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")],
    ])


def get_experience_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔰 Я новичок", callback_data="exp_beginner"),
            InlineKeyboardButton(text="💪 1-2 года", callback_data="exp_1_2"),
        ],
        [
            InlineKeyboardButton(text="🏋️ 2-3 года", callback_data="exp_2_3"),
            InlineKeyboardButton(text="🔥 3+ лет", callback_data="exp_3_plus"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_start")],
    ])


def get_progress_keyboard(step: int, total: int, back_callback: str = "back_to_start") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🔙 Назад ({step}/{total})",
            callback_data=back_callback
        )]
    ])