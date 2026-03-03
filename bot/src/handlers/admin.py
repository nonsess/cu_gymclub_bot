import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.utils.admin import is_admin
from src.api.client import backend_client
from src.keyboards.admin import (
    get_admin_menu_keyboard,
    get_cancel_keyboard,
    get_export_keyboard,
    get_ban_confirm_keyboard,
    get_broadcast_confirm_keyboard,
)

router = Router()
logger = logging.getLogger(__name__)


class AdminStates(StatesGroup):
    waiting_for_broadcast_message = State()
    waiting_for_broadcast_confirm = State()
    waiting_for_ban_user_id = State()


@router.message(F.text == "📢 Рассылка")
async def admin_broadcast_start(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.set_state(AdminStates.waiting_for_broadcast_message)
    
    await message.answer(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Отправьте текст рассылки (поддерживает HTML):\n\n"
        "<i>Пример:</i>\n"
        "<code>🎉 <b>Новое обновление!</b>\nЗаходите в бота!</code>\n\n"
        "⚠️ Максимум 4096 символов",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AdminStates.waiting_for_broadcast_message)
async def admin_broadcast_receive(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("✅ Отменено.", reply_markup=get_admin_menu_keyboard())
        return
    
    text = message.text.strip()
    
    if len(text) > 4096:
        await message.answer("⚠️ Текст слишком длинный (максимум 4096 символов).")
        return
    
    if len(text) < 5:
        await message.answer("⚠️ Текст слишком короткий (минимум 5 символов).")
        return
    
    await state.update_data(broadcast_message=text)
    await state.set_state(AdminStates.waiting_for_broadcast_confirm)
    
    preview = text[:500] + ("..." if len(text) > 500 else "")
    
    await message.answer(
        f"⚠️ <b>Подтверждение рассылки</b>\n\n"
        f"📝 <b>Текст сообщения:</b>\n"
        f"<code>{preview}</code>\n\n"
        f"📊 <b>Действие:</b>\n"
        f"• Сообщение будет отправлено всем активным пользователям\n"
        f"• Статистика придёт вам в ЛС после завершения\n"
        f"• <b>Нельзя отменить после запуска</b>\n\n"
        f"Подтверждаете отправку?",
        parse_mode="HTML",
        reply_markup=get_broadcast_confirm_keyboard()
    )


@router.callback_query(F.data == "broadcast_confirm")
async def admin_broadcast_execute(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id

    if not is_admin(telegram_id):
        await callback.answer()
        return
    
    data = await state.get_data()
    text = data.get("broadcast_message")
    
    if not text:
        await callback.answer("⚠️ Ошибка: текст рассылки не найден", show_alert=True)
        return
    
    await backend_client.start_broadcast(telegram_id, text)
    
    await state.clear()
    
    await callback.message.answer(
        f"✅ <b>Рассылка запущена!</b>\n\n"
        "Статистика придёт вам в личные сообщения по завершении.",
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard()
    )
    
    try:
        await callback.message.delete()
    except:
        pass


@router.callback_query(F.data == "broadcast_cancel")
async def admin_broadcast_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    await callback.message.answer(
        "✅ Рассылка отменена.",
        reply_markup=get_admin_menu_keyboard()
    )
    
    try:
        await callback.message.delete()
    except:
        pass


@router.message(F.text == "📥 Экспорт CSV")
async def admin_export_csv(message: types.Message):
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📥 <b>Экспорт профилей</b>\n\n"
        "Выберите тип экспорта:",
        reply_markup=get_export_keyboard()
    )


@router.callback_query(F.data.startswith("export_"))
async def admin_export_callback(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id

    if not is_admin(telegram_id):
        await callback.answer()
        return
    
    action = callback.data.split("_")[1]
    
    if action == "cancel":
        await callback.message.edit_text("✅ Отменено.", reply_markup=get_admin_menu_keyboard())
        await callback.answer()
        return
    
    params_map = {
        "all": {},
        "active": {"is_active": "true"},
        "inactive": {"is_active": "false"},
    }
    
    await callback.message.answer("⏳ Загружаю данные...")
    
    csv_content = await backend_client.export_profiles(
        telegram_id=telegram_id,
        params=params_map.get(action, {})
    )
    
    await callback.message.answer_document(
        document=types.BufferedInputFile(
            csv_content.encode('utf-8-sig'),
            filename=f"profiles_{action}.csv"
        ),
        caption=f"✅ Экспорт завершён\n📊 Строк: {len(csv_content.split(chr(10))) - 1}",
        reply_markup=get_admin_menu_keyboard()
    )
    
    await callback.message.delete()


@router.message(F.text == "🚫 Забанить пользователя")
async def admin_ban_start(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.set_state(AdminStates.waiting_for_ban_user_id)
    
    await message.answer(
        "🚫 <b>Бан пользователя</b>\n\n"
        "Отправьте <b>USER_ID</b> пользователя для бана:\n\n"
        "⚠️ <b>Важно:</b> это USER_ID из базы данных, НЕ Telegram ID!\n\n"
        "Можно узнать из CSV экспорта (колонка `user_id`).",
        parse_mode="HTML",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AdminStates.waiting_for_ban_user_id)
async def admin_ban_confirm(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("✅ Отменено.", reply_markup=get_admin_menu_keyboard())
        return
    
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Введите корректный числовой USER_ID.")
        return
    
    await state.update_data(ban_user_id=user_id)
    
    await message.answer(
        f"⚠️ <b>Подтверждение бана</b>\n\n"
        f"Вы собираетесь забанить пользователя с <b>USER_ID: {user_id}</b>\n\n"
        "Это действие:\n"
        "• Заблокирует пользователя\n"
        "• Деактивирует его профиль\n"
        "• <b>Нельзя отменить</b>\n\n"
        "Подтверждаете?",
        parse_mode="HTML",
        reply_markup=get_ban_confirm_keyboard(user_id)
    )


@router.callback_query(F.data.startswith("ban_confirm_"))
async def admin_ban_execute(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    
    if not is_admin(telegram_id):
        await callback.answer()
        return
    
    user_id = int(callback.data.split("_")[2])
    
    await backend_client.ban_user(telegram_id, user_id)
    
    await state.clear()
    
    await callback.message.answer(
        f"✅ <b>Пользователь с USER_ID {user_id} забанен!</b>",
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard()
    )
    
    try:
        await callback.message.delete()
    except:
        pass


@router.callback_query(F.data == "ban_cancel")
async def admin_ban_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    await callback.message.answer(
        "✅ Отменено.",
        reply_markup=get_admin_menu_keyboard()
    )
    
    try:
        await callback.message.delete()
    except:
        pass


@router.message(F.text == "🔙 В главное меню")
async def admin_back_to_main(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.clear()
    
    from src.handlers.start import show_main_menu
    await show_main_menu(message, message.from_user.id)