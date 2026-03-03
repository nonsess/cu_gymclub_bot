from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Рассылка")],
            [KeyboardButton(text="📥 Экспорт CSV")],
            [KeyboardButton(text="🚫 Забанить пользователя")],
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


def get_ban_confirm_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚫 Забанить", callback_data=f"ban_confirm_{user_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="ban_cancel"),
        ]
    ])


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Отправить", callback_data="broadcast_confirm"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel"),
        ]
    ])