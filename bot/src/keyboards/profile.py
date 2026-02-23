from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_start_keyboard(has_profile: bool = False) -> InlineKeyboardMarkup:
    keyboard = []
    
    if has_profile:
        keyboard = [
            [
                InlineKeyboardButton(text="🔍 Смотреть анкеты", callback_data="start_swiping"),
            ],
            [
                InlineKeyboardButton(text="👤 Моя анкета", callback_data="my_profile"),
                InlineKeyboardButton(text="❤️ Входящие лайки", callback_data="check_incoming"),
            ],
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton(text="📝 Создать анкету", callback_data="create_profile"),
            ],
        ]
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


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


def get_back_keyboard(callback_data: str = "back_to_start") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
    ])