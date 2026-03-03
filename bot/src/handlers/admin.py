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
)

router = Router()
logger = logging.getLogger(__name__)


class AdminStates(StatesGroup):
    waiting_for_broadcast_message = State()


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
async def admin_broadcast_send(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    
    if not is_admin(telegram_id):
        return
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("✅ Отменено.", reply_markup=get_admin_menu_keyboard())
        return
    
    text = message.text.strip()
    
    if len(text) > 4096:
        await message.answer("⚠️ Текст слишком длинный (максимум 4096 символов).")
        return
    
    await backend_client.start_broadcast(telegram_id, text)
    
    await state.clear()
    
    await message.answer(
        f"✅ <b>Рассылка запущена!</b>\n\n"
        "Статистика придёт вам в личные сообщения по завершении.",
        parse_mode="HTML",
        reply_markup=get_admin_menu_keyboard()
    )

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

@router.message(F.text == "🔙 В главное меню")
async def admin_back_to_main(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    
    await state.clear()
    
    from src.handlers.start import show_main_menu
    await show_main_menu(message, message.from_user.id)