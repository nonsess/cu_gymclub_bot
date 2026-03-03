from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Рассылка")],
            [KeyboardButton(text="📥 Экспорт CSV")],
            [KeyboardButton(text="🔙 В главное меню")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Админ-панель 👇"
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_export_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Все профили", callback_data="export_all")],
        [InlineKeyboardButton(text="✅ Активные", callback_data="export_active")],
        [InlineKeyboardButton(text="⏸ Неактивные", callback_data="export_inactive")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="export_cancel")],
    ])