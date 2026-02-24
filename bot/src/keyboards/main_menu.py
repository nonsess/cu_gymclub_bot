from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_menu_keyboard(has_profile: bool = False) -> ReplyKeyboardMarkup:
    buttons = []
    
    if has_profile:
        buttons = [
            [KeyboardButton(text="🔍 Начать свайпать")],
            [
                KeyboardButton(text="👤 Моя анкета"),
                KeyboardButton(text="❤️ Входящие лайки"),
            ]
        ]
    else:
        buttons = [
            [KeyboardButton(text="📝 Создать анкету")],
        ]
        
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие 👇"
    )


def get_reply_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def hide_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove(remove_keyboard=True)