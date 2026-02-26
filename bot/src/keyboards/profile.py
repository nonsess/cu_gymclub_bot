from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)


def get_profile_actions_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Редактировать анкету")],
            [KeyboardButton(text="Скрыть анкету")],
            [KeyboardButton(text="🔙 Вернуться в главное меню")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие 👇"
    )


def get_edit_choice_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Изменить описание")],
            [KeyboardButton(text="🎂 Изменить возраст")],
            [KeyboardButton(text="💪 Изменить опыт")],
            [KeyboardButton(text="📷 Изменить фото")],
            [KeyboardButton(text="👤 Изменить имя")],
            [KeyboardButton(text="✅ Завершить редактирование")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери, что хочешь изменить 👇"
    )


def get_gender_keyboard(current_gender: str = None) -> ReplyKeyboardMarkup:
    buttons = []
    
    if current_gender:
        current_text = "👨 Парень (текущий)" if current_gender == "male" else "👩 Девушка (текущий)"
        buttons.append([KeyboardButton(text=current_text)])
    
    buttons.extend([
        [KeyboardButton(text="👨 Парень"), KeyboardButton(text="👩 Девушка")],
        [KeyboardButton(text="🔙 Отмена")]
    ])
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выбери пол или нажми Отмена 👇"
    )


def get_experience_keyboard(current_exp: str = None) -> ReplyKeyboardMarkup:
    exp_options = [
        ("🔰 Я новичок", "beginner"),
        ("💪 1-2 года", "1_2"),
        ("🏋️ 2-3 года", "2_3"),
        ("🔥 3+ лет", "3_plus")
    ]
    
    exp_labels = {
        "beginner": "🔰 Я новичок",
        "1_2": "💪 1-2 года",
        "2_3": "🏋️ 2-3 года",
        "3_plus": "🔥 3+ лет"
    }
    
    buttons = []
    
    if current_exp and current_exp in exp_labels:
        buttons.append([KeyboardButton(text=f"{exp_labels[current_exp]} (текущий)")])
    
    row = []
    for i, (text, value) in enumerate(exp_options):
        row.append(KeyboardButton(text=text))
        if i % 2 == 1:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([KeyboardButton(text="🔙 Отмена")])
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выбери свой опыт 👇"
    )


def get_photo_edit_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📷 Загрузить новые фото")],
            [KeyboardButton(text="💾 Оставить текущие фото")],
            [KeyboardButton(text="🔙 Отмена")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие с фото 👇"
    )


def get_photo_upload_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Завершить загрузку фото")],
            [KeyboardButton(text="🔙 Отмена")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Отправляй фото (до 3 шт) 👇"
    )


def get_name_keyboard(first_name: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=first_name)],
            [KeyboardButton(text="🔙 Отмена")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Напиши имя или выбери из профиля 👇"
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Отмена")]],
        resize_keyboard=True
    )


def hide_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def get_confirmation_keyboard(confirm_text: str, cancel_text: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=confirm_text)],
            [KeyboardButton(text=cancel_text)]
        ],
        resize_keyboard=True
    )


def get_inline_back_keyboard(callback_data: str = "back_to_start") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
    ])
