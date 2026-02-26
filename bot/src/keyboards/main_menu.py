from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


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

def return_my_profile_active() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Вернуться назад")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Возвращайся 👇"
    )
