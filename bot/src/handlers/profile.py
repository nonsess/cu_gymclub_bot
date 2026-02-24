import logging
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.api.client import backend_client
from src.keyboards.main_menu import get_main_menu_keyboard, get_reply_back_keyboard, hide_keyboard
from src.keyboards.profile import (
    get_profile_menu_keyboard,
    get_edit_profile_keyboard,
    get_confirmation_keyboard,
    get_inline_back_keyboard,
    get_gender_keyboard,
    get_experience_keyboard,
    get_progress_keyboard,
)

router = Router()
logger = logging.getLogger(__name__)


class ProfileStates(StatesGroup):
    # Создание анкеты
    waiting_for_name = State()
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_experience = State()
    waiting_for_about = State()
    waiting_for_photo = State()
    
    # Редактирование анкеты
    waiting_for_new_description = State()
    waiting_for_new_gender = State()
    waiting_for_new_age = State()
    waiting_for_new_experience = State()
    waiting_for_delete_confirm = State()


async def _safe_callback_answer(
    callback: types.CallbackQuery,
    text: str,
    reply_markup=None,
    parse_mode: str = "HTML",
    delete_old: bool = True
):
    await callback.message.answer(
        text,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )
    
    if delete_old:
        try:
            await callback.message.delete()
        except Exception as e:
            logger.debug(f"Could not delete old message: {e}")


async def _send_profile_view(
    target: types.CallbackQuery | types.Message,
    profile: dict,
    edit_mode: bool = True
):
    gender_text = "👨 Парень" if profile['gender'] == 'male' else "👩 Девушка"
    status_text = "✅ Активна" if profile['is_active'] else "⏸ Скрыта"
    
    desc_parts = profile['description'].split('\n\n🏋️ Опыт тренировок:')
    main_desc = desc_parts[0]
    experience = desc_parts[1] if len(desc_parts) > 1 else None
    
    text = (
        f"👤 <b>Ваша анкета</b>\n\n"
        f"📝 <b>Описание:</b>\n{main_desc}\n\n"
        f"{f'🏋️ <b>Опыт:</b> {experience}\n' if experience else ''}"
        f"{gender_text}\n"
        f"{status_text}"
    )
    
    is_callback = isinstance(target, types.CallbackQuery)
    
    try:
        if profile.get('photo_ids') and profile['photo_ids']:
            photo = profile['photo_ids'][0]
            if edit_mode and is_callback:
                try:
                    await target.message.edit_media(
                        media=types.InputMediaPhoto(media=photo, caption=text, parse_mode="HTML"),
                        reply_markup=get_profile_menu_keyboard()
                    )
                    return
                except:
                    pass
            await target.answer_photo(
                photo=photo,
                caption=text,
                parse_mode="HTML",
                reply_markup=get_profile_menu_keyboard()
            )
        else:
            if edit_mode and is_callback:
                try:
                    await target.message.edit_text(
                        text,
                        reply_markup=get_profile_menu_keyboard(),
                        parse_mode="HTML"
                    )
                    return
                except:
                    pass
            await target.answer(
                text,
                reply_markup=get_profile_menu_keyboard(),
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error sending profile view: {e}")
        await target.answer("⚠️ Ошибка отображения анкеты", reply_markup=get_profile_menu_keyboard())


@router.callback_query(F.data == "create_profile")
async def start_create_profile(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    await callback.message.edit_text(
        "📝 <b>Создание анкеты</b>\n\n"
        "👋 <b>Шаг 1 из 6</b>\n\n"
        "Как тебя зовут?",
        parse_mode="HTML",
        reply_markup=get_inline_back_keyboard("back_to_start")
    )
    await state.set_state(ProfileStates.waiting_for_name)


async def start_create_profile_from_menu(
    message: types.Message,
    telegram_id: int,
    state: FSMContext
):
    await state.clear()
    
    await message.answer(
        "📝 <b>Создание анкеты</b>\n\n"
        "👋 <b>Шаг 1 из 6</b>\n\n"
        "Как тебя зовут?",
        parse_mode="HTML",
        reply_markup=get_reply_back_keyboard()
    )
    await state.set_state(ProfileStates.waiting_for_name)


@router.message(ProfileStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        from src.handlers.start import show_main_menu
        await show_main_menu(message, message.from_user.id)
        return
    
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("⚠️ Имя слишком короткое. Введи корректное имя:")
        return
    if len(name) > 50:
        await message.answer("⚠️ Имя слишком длинное (максимум 50 символов).")
        return
    
    await state.update_data(name=name)
    
    await message.answer(
        f"✅ Привет, <b>{name}</b>!\n\n"
        f"👤 <b>Шаг 2 из 6</b>\n\n"
        "Выбери свой пол:",
        parse_mode="HTML",
        reply_markup=get_gender_keyboard()
    )
    await state.set_state(ProfileStates.waiting_for_gender)


@router.callback_query(F.data.startswith("gender_"), StateFilter(ProfileStates.waiting_for_gender))
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    await callback.answer()
    
    await callback.message.edit_text(
        "✅ Пол сохранён!\n\n"
        f"🎂 <b>Шаг 3 из 6</b>\n\n"
        "Сколько тебе лет? (от 16 до 100)",
        parse_mode="HTML",
        reply_markup=get_progress_keyboard(3, 6)
    )
    await state.set_state(ProfileStates.waiting_for_age)


@router.message(ProfileStates.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        from src.handlers.start import show_main_menu
        await show_main_menu(message, message.from_user.id)
        return
    
    try:
        age = int(message.text.strip())
        if age < 16 or age > 100:
            await message.answer("⚠️ Возраст должен быть от 16 до 100 лет.\nПопробуй ещё раз:")
            return
        
        await state.update_data(age=age)
        
        await message.answer(
            f"✅ Возраст: <b>{age} лет</b>\n\n"
            f"💪 <b>Шаг 4 из 6</b>\n\n"
            "Как давно ты тренируешься?",
            parse_mode="HTML",
            reply_markup=get_experience_keyboard()
        )
        await state.set_state(ProfileStates.waiting_for_experience)
        
    except ValueError:
        await message.answer("⚠️ Это не число. Введите возраст цифрами:")


@router.callback_query(F.data.startswith("exp_"), StateFilter(ProfileStates.waiting_for_experience))
async def process_experience(callback: types.CallbackQuery, state: FSMContext):
    exp_data = callback.data.split("_", 1)[1]
    experience_labels = {
        "beginner": "Я новичок",
        "1_2": "1-2 года",
        "2_3": "2-3 года",
        "3_plus": "3+ лет"
    }
    experience_text = experience_labels.get(exp_data, exp_data)
    
    await state.update_data(experience=experience_text)
    await callback.answer()
    
    await callback.message.edit_text(
        f"✅ Опыт: <b>{experience_text}</b>\n\n"
        f"📍 <b>Шаг 5 из 6</b>\n\n"
        "<b>О себе</b>\n\n"
        "Укажи:\n"
        "• В какой зал ты ходишь\n"
        "• В какие дни и время\n"
        "• Несколько слов о себе\n\n"
        "<b>Пример:</b>\n"
        "<i>Качалка в ЦУ, пн-ср-пт, 15.00-17.00, качаю только бицуху</i>\n\n"
        "⚠️ <b>Указывай большой промежуток времени — так бот лучше подберёт партнёра!</b>",
        parse_mode="HTML",
        reply_markup=get_progress_keyboard(5, 6)
    )
    await state.set_state(ProfileStates.waiting_for_about)


@router.message(ProfileStates.waiting_for_about)
async def process_about(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        from src.handlers.start import show_main_menu
        await show_main_menu(message, message.from_user.id)
        return
    
    about = message.text.strip()
    
    if len(about) < 10:
        await message.answer("⚠️ Описание слишком короткое (минимум 10 символов).\nРасскажи подробнее:")
        return
    
    data = await state.get_data()
    experience = data.get("experience", "")
    full_description = f"{about}\n\n🏋️ Опыт тренировок: {experience}"
    
    if len(full_description) > 1000:
        await message.answer(f"⚠️ Описание слишком длинное ({len(full_description)} символов, макс. 1000).\nСократи немного:")
        return
    
    await state.update_data(description=full_description)
    
    await message.answer(
        "✅ Описание сохранено!\n\n"
        f"📷 <b>Шаг 6 из 6</b>\n\n"
        "Отправь фото для анкеты (<i>необязательно</i>).\n"
        "Можно отправить одно или несколько фото.\n"
        "Когда закончишь — нажми «Готово».",
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Готово", callback_data="photo_done")]
        ])
    )
    await state.set_state(ProfileStates.waiting_for_photo)


@router.message(ProfileStates.waiting_for_photo)
async def process_photo(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        from src.handlers.start import show_main_menu
        await show_main_menu(message, message.from_user.id)
        return
    
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document and message.document.mime_type.startswith('image/'):
        file_id = message.document.file_id
    else:
        await message.answer("⚠️ Пожалуйста, отправь фото или нажми «Готово».")
        return
    
    data = await state.get_data()
    photo_ids = data.get("photo_ids", [])
    photo_ids.append(file_id)
    await state.update_data(photo_ids=photo_ids)
    
    await message.answer(
        f"✅ Фото добавлено! ({len(photo_ids)} шт.)\n"
        "Отправляй ещё или нажми «Готово».",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Готово", callback_data="photo_done")]
        ])
    )


@router.callback_query(F.data == "photo_done", StateFilter(ProfileStates.waiting_for_photo))
async def finish_photo(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    telegram_id = callback.from_user.id
    
    profile_data = {
        "name": data.get("name"),
        "description": data.get("description"),
        "gender": data.get("gender"),
        "age": data.get("age"),
        "photo_ids": data.get("photo_ids", [])
    }
    
    logger.info(f"Creating profile for user {telegram_id}: {profile_data}")
    
    try:
        await backend_client.create_profile(telegram_id, profile_data)
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        await callback.message.edit_text(
            "⚠️ Ошибка при создании анкеты. Попробуй позже.",
            reply_markup=get_inline_back_keyboard("back_to_start")
        )
        await state.clear()
        return
    
    await state.clear()
    
    await callback.message.answer(
        "🎉 <b>Анкета создана!</b>\n\n"
        "Теперь ты можешь искать партнёров для тренировок.\n"
        "Нажми «🔍 Начать свайпать», чтобы увидеть анкеты!",
        reply_markup=get_main_menu_keyboard(has_profile=True),
        parse_mode="HTML"
    )
    
    try:
        await callback.message.delete()
    except:
        pass


@router.callback_query(F.data == "my_profile")
async def show_my_profile(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id
    try:
        profile = await backend_client.get_profile(telegram_id)
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        await callback.answer("⚠️ Ошибка загрузки анкеты", show_alert=True)
        return
    
    if not profile:
        await callback.message.edit_text(
            "У вас нет анкеты. Создайте её!",
            reply_markup=get_main_menu_keyboard(has_profile=False)
        )
        return
    
    await _send_profile_view(callback, profile, edit_mode=True)


async def show_my_profile_message(message: types.Message, telegram_id: int):
    try:
        profile = await backend_client.get_profile(telegram_id)
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        await message.answer("⚠️ Ошибка загрузки анкеты", reply_markup=get_main_menu_keyboard(has_profile=True))
        return
    
    if not profile:
        await message.answer("У вас нет анкеты. Создайте её!", reply_markup=get_main_menu_keyboard(has_profile=False))
        return
    
    await _send_profile_view(message, profile, edit_mode=False)


@router.callback_query(F.data == "edit_profile")
async def start_edit_profile(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    await _safe_callback_answer(
        callback,
        "✏️ <b>Редактирование анкеты</b>\n\n"
        "Что хотите изменить?",
        reply_markup=get_edit_profile_keyboard()
    )


@router.callback_query(F.data == "edit_description")
async def edit_description_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Введите новое описание:\n\n"
        "<i>Укажи зал, дни, время и пару слов о себе</i>\n\n"
        "⚠️ Максимум 1000 символов",
        parse_mode="HTML"
    )
    await state.set_state(ProfileStates.waiting_for_new_description)


@router.message(ProfileStates.waiting_for_new_description)
async def process_new_description(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("✅ Отменено.", reply_markup=get_profile_menu_keyboard())
        return
    
    description = message.text.strip()
    if len(description) < 10:
        await message.answer("⚠️ Описание слишком короткое (минимум 10 символов).")
        return
    if len(description) > 1000:
        await message.answer(f"⚠️ Описание слишком длинное ({len(description)} символов, макс. 1000).")
        return
    
    telegram_id = message.from_user.id
    try:
        await backend_client.update_profile(telegram_id, {"description": description})
    except Exception as e:
        logger.error(f"Error updating description: {e}")
        await message.answer("⚠️ Ошибка при обновлении.")
        await state.clear()
        return
    
    await state.clear()
    await message.answer("✅ Описание обновлено!", reply_markup=get_profile_menu_keyboard())


@router.callback_query(F.data == "edit_age")
async def edit_age_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🎂 Введите новый возраст (16-100):")
    await state.set_state(ProfileStates.waiting_for_new_age)


@router.message(ProfileStates.waiting_for_new_age)
async def process_new_age(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("✅ Отменено.", reply_markup=get_profile_menu_keyboard())
        return
    
    try:
        age = int(message.text.strip())
        if age < 16 or age > 100:
            await message.answer("⚠️ Возраст должен быть от 16 до 100 лет.")
            return
        
        telegram_id = message.from_user.id
        await backend_client.update_profile(telegram_id, {"age": age})
        await state.clear()
        await message.answer(f"✅ Возраст обновлён: {age} лет", reply_markup=get_profile_menu_keyboard())
    except ValueError:
        await message.answer("⚠️ Это не число. Введите возраст цифрами:")


@router.callback_query(F.data == "delete_profile")
async def confirm_delete(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "⚠️ <b>Удаление анкеты</b>\n\n"
        "Вы уверены? Это действие нельзя отменить.",
        reply_markup=get_confirmation_keyboard("delete_profile_confirm", "back_to_profile"),
        parse_mode="HTML"
    )
    await state.set_state(ProfileStates.waiting_for_delete_confirm)


@router.callback_query(F.data == "delete_profile_confirm")
async def delete_profile(callback: types.CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    try:
        await backend_client.update_profile(telegram_id, {"is_active": False})
    except Exception as e:
        logger.error(f"Error deleting profile: {e}")
        await callback.answer("⚠️ Ошибка при удалении", show_alert=True)
        return
    
    await state.clear()
    
    await callback.message.answer(
        "🗑 Анкета удалена.",
        reply_markup=get_main_menu_keyboard(has_profile=False)
    )
    
    try:
        await callback.message.delete()
    except:
        pass


@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await show_my_profile(callback)


@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    telegram_id = callback.from_user.id
    profile = await backend_client.get_profile(telegram_id)
    
    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_menu_keyboard(has_profile=bool(profile))
    )
    
    try:
        await callback.message.delete()
    except:
        pass