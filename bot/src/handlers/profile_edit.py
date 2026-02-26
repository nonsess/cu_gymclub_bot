import logging
from aiogram import F, types, Router
from aiogram.fsm.context import FSMContext

from src.api.client import backend_client
from src.keyboards.main_menu import get_main_menu_keyboard, return_my_profile_active
from src.keyboards.profile import (
    get_edit_choice_keyboard,
    get_confirmation_keyboard,
    get_gender_keyboard,
    get_experience_keyboard,
    get_name_keyboard,
    get_photo_edit_keyboard,
    get_photo_upload_keyboard,
    get_cancel_keyboard,
    hide_keyboard
)
from src.states.profile import ProfileStates

router = Router()
logger = logging.getLogger(__name__)


def _extract_description(full_description: str) -> str:
    if '🏋️ Опыт тренировок:' in full_description:
        return full_description.split('\n\n🏋️ Опыт тренировок:')[0]
    return full_description


def _extract_experience(description: str) -> str:
    if '🏋️ Опыт тренировок:' in description:
        return description.split('🏋️ Опыт тренировок:')[-1].strip()
    return "Не указан"


def _get_experience_key(full_description: str) -> str:
    if '🏋️ Опыт тренировок:' not in full_description:
        return None
    
    exp_text = full_description.split('🏋️ Опыт тренировок:')[-1].strip()
    
    exp_mapping = {
        "Я новичок": "beginner",
        "1-2 года": "1_2",
        "2-3 года": "2_3",
        "3+ лет": "3_plus"
    }
    
    for text, key in exp_mapping.items():
        if text in exp_text:
            return key
    return None


@router.message(F.text == "✏️ Редактировать анкету")
async def start_edit_from_keyboard(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    profile = await backend_client.get_profile(telegram_id)
    
    if not profile:
        await message.answer("❌ Анкета не найдена")
        return
    
    await state.update_data(original_profile=profile)
    
    await message.answer(
        "✏️ <b>Редактирование анкеты</b>\n\n"
        "Выбери, что хочешь изменить, используя кнопки ниже:\n\n"
        f"👤 Имя: <b>{profile.get('name', 'Не указано')}</b>\n"
        f"👤 Пол: <b>{'👨 Парень' if profile.get('gender') == 'male' else '👩 Девушка'}</b>\n"
        f"🎂 Возраст: <b>{profile.get('age', 'Не указан')}</b>\n"
        f"💪 Опыт: <b>{_extract_experience(profile.get('description', ''))}</b>\n"
        f"📷 Фото: <b>{len(profile.get('media', []))}/3</b>",
        parse_mode="HTML",
        reply_markup=get_edit_choice_keyboard()
    )
    await state.set_state(ProfileStates.editing_profile)


@router.message(ProfileStates.editing_profile, F.text.in_(["📷 Загрузить новые фото", "💾 Оставить текущие фото"]))
async def handle_photo_actions(message: types.Message, state: FSMContext):
    if message.text == "📷 Загрузить новые фото":
        await upload_new_photos(message, state)
    elif message.text == "💾 Оставить текущие фото":
        await keep_current_photos(message, state)


@router.message(ProfileStates.editing_profile, F.text)
async def process_edit_choice(message: types.Message, state: FSMContext):
    """Общий хендлер для остальных полей редактирования"""
    choice = message.text
    data = await state.get_data()
    profile = data.get('original_profile', {})
    
    if choice == "📝 Изменить описание":
        await message.answer(
            "📝 <b>Редактирование описания</b>\n\n"
            "Текущее описание:\n"
            f"<i>{_extract_description(profile.get('description', ''))}</i>\n\n"
            "Введи новое описание (минимум 10 символов):\n\n"
            "<i>Укажи зал, дни, время и пару слов о себе</i>",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(ProfileStates.waiting_for_new_about)
        
    elif choice == "🎂 Изменить возраст":
        await message.answer(
            f"🎂 <b>Редактирование возраста</b>\n\n"
            f"Текущий возраст: <b>{profile.get('age', 'Не указан')}</b>\n\n"
            "Введи новый возраст (16-100):",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(ProfileStates.waiting_for_new_age)
        
    elif choice == "👤 Изменить пол":
        current_gender = profile.get('gender')
        await message.answer(
            "👤 <b>Редактирование пола</b>\n\n"
            "Выбери новый пол:",
            parse_mode="HTML",
            reply_markup=get_gender_keyboard(current_gender)
        )
        await state.set_state(ProfileStates.waiting_for_new_gender)
        
    elif choice == "💪 Изменить опыт":
        current_exp = _get_experience_key(profile.get('description', ''))
        await message.answer(
            "💪 <b>Редактирование опыта</b>\n\n"
            "Выбери новый уровень опыта:",
            parse_mode="HTML",
            reply_markup=get_experience_keyboard(current_exp)
        )
        await state.set_state(ProfileStates.waiting_for_new_experience)
        
    elif choice == "📷 Изменить фото":
        await edit_photos_start(message, state)
        
    elif choice == "👤 Изменить имя":
        await message.answer(
            f"👤 <b>Редактирование имени</b>\n\n"
            f"Текущее имя: <b>{profile.get('name', 'Не указано')}</b>\n\n"
            "Введи новое имя:",
            parse_mode="HTML",
            reply_markup=get_name_keyboard(profile.get('name', ''))
        )
        await state.set_state(ProfileStates.waiting_for_new_name)
        
    elif choice == "✅ Завершить редактирование":
        await finish_editing(message, state)
        
    else:
        await message.answer("❌ Непонятный выбор. Используй кнопки ниже.")


@router.message(ProfileStates.waiting_for_new_name)
async def process_new_name(message: types.Message, state: FSMContext):
    if message.text == "🔙 Отмена":
        await return_to_edit_menu(message, state)
        return
    
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("⚠️ Имя слишком короткое. Введи корректное имя:")
        return
    if len(name) > 50:
        await message.answer("⚠️ Имя слишком длинное (максимум 50 символов).")
        return
    
    telegram_id = message.from_user.id
    try:
        await backend_client.update_profile(telegram_id, {"name": name})
        
        data = await state.get_data()
        profile = data.get('original_profile', {})
        profile['name'] = name
        await state.update_data(original_profile=profile)
        
        await message.answer(
            f"✅ Имя изменено на <b>{name}</b>!",
            parse_mode="HTML",
            reply_markup=hide_keyboard()
        )
        await return_to_edit_menu(message, state)
        
    except Exception as e:
        logger.error(f"Error updating name: {e}")
        await message.answer("❌ Ошибка при обновлении имени. Попробуй позже.")


@router.message(ProfileStates.waiting_for_new_age)
async def process_new_age(message: types.Message, state: FSMContext):
    if message.text == "🔙 Отмена":
        await return_to_edit_menu(message, state)
        return
    
    try:
        age = int(message.text.strip())
        if age < 16 or age > 100:
            await message.answer("⚠️ Возраст должен быть от 16 до 100 лет.")
            return
        
        telegram_id = message.from_user.id
        await backend_client.update_profile(telegram_id, {"age": age})
        
        data = await state.get_data()
        profile = data.get('original_profile', {})
        profile['age'] = age
        await state.update_data(original_profile=profile)
        
        await message.answer(
            f"✅ Возраст обновлён: {age} лет",
            reply_markup=hide_keyboard()
        )
        await return_to_edit_menu(message, state)
        
    except ValueError:
        await message.answer("⚠️ Это не число. Введите возраст цифрами:")


@router.message(ProfileStates.waiting_for_new_gender, F.text)
async def process_new_gender(message: types.Message, state: FSMContext):
    if message.text == "🔙 Отмена":
        await return_to_edit_menu(message, state)
        return
    
    gender_map = {
        "👨 Парень": "male",
        "👩 Девушка": "female",
        "👨 Парень (текущий)": None,
        "👩 Девушка (текущий)": None
    }
    
    if message.text not in gender_map:
        await message.answer("⚠️ Пожалуйста, выбери пол из кнопок ниже:")
        return
    
    if "(текущий)" in message.text:
        await return_to_edit_menu(message, state)
        return
    
    gender = gender_map[message.text]
    
    telegram_id = message.from_user.id
    try:
        await backend_client.update_profile(telegram_id, {"gender": gender})
        
        data = await state.get_data()
        profile = data.get('original_profile', {})
        profile['gender'] = gender
        await state.update_data(original_profile=profile)
        
        gender_text = "👨 Парень" if gender == "male" else "👩 Девушка"
        await message.answer(
            f"✅ Пол изменён на {gender_text}!",
            reply_markup=hide_keyboard()
        )
        await return_to_edit_menu(message, state)
        
    except Exception as e:
        logger.error(f"Error updating gender: {e}")
        await message.answer("❌ Ошибка при обновлении пола. Попробуй позже.")


@router.message(ProfileStates.waiting_for_new_experience, F.text)
async def process_new_experience(message: types.Message, state: FSMContext):
    if message.text == "🔙 Отмена":
        await return_to_edit_menu(message, state)
        return
    
    exp_map = {
        "🔰 Я новичок": "beginner",
        "💪 1-2 года": "1_2",
        "🏋️ 2-3 года": "2_3",
        "🔥 3+ лет": "3_plus"
    }
    
    exp_labels = {
        "beginner": "Я новичок",
        "1_2": "1-2 года",
        "2_3": "2-3 года",
        "3_plus": "3+ лет"
    }
    
    if "(текущий)" in message.text:
        await return_to_edit_menu(message, state)
        return
    
    if message.text not in exp_map:
        await message.answer("⚠️ Пожалуйста, выбери уровень опыта из кнопок ниже:")
        return
    
    exp_key = exp_map[message.text]
    experience_text = exp_labels[exp_key]
    
    data = await state.get_data()
    profile = data.get('original_profile', {})
    current_description = profile.get('description', '')
    
    base_description = _extract_description(current_description)
    new_description = f"{base_description}\n\n🏋️ Опыт тренировок: {experience_text}"
    
    telegram_id = message.from_user.id
    try:
        await backend_client.update_profile(telegram_id, {"description": new_description})
        
        profile['description'] = new_description
        await state.update_data(original_profile=profile)
        
        await message.answer(
            f"✅ Опыт изменён на: <b>{experience_text}</b>!",
            parse_mode="HTML",
            reply_markup=hide_keyboard()
        )
        await return_to_edit_menu(message, state)
        
    except Exception as e:
        logger.error(f"Error updating experience: {e}")
        await message.answer("❌ Ошибка при обновлении опыта. Попробуй позже.")


@router.message(ProfileStates.waiting_for_new_about)
async def process_new_about(message: types.Message, state: FSMContext):
    if message.text == "🔙 Отмена":
        await return_to_edit_menu(message, state)
        return
    
    about = message.text.strip()
    
    if len(about) < 10:
        await message.answer("⚠️ Описание слишком короткое (минимум 10 символов).")
        return
    
    data = await state.get_data()
    profile = data.get('original_profile', {})
    current_exp = _extract_experience(profile.get('description', ''))
    
    new_description = f"{about}\n\n🏋️ Опыт тренировок: {current_exp}"
    
    if len(new_description) > 1000:
        await message.answer(f"⚠️ Описание слишком длинное ({len(new_description)} символов, макс. 1000).\nСократи немного:")
        return
    
    telegram_id = message.from_user.id
    try:
        await backend_client.update_profile(telegram_id, {"description": new_description})
        
        profile['description'] = new_description
        await state.update_data(original_profile=profile)
        
        await message.answer(
            "✅ Описание обновлено!",
            reply_markup=hide_keyboard()
        )
        await return_to_edit_menu(message, state)
        
    except Exception as e:
        logger.error(f"Error updating description: {e}")
        await message.answer("❌ Ошибка при обновлении описания. Попробуй позже.")


async def edit_photos_start(message: types.Message, state: FSMContext):
    data = await state.get_data()
    profile = data.get('original_profile', {})
    media_count = len(profile.get('media', []))
    
    await message.answer(
        f"📷 <b>Редактирование фото</b>\n\n"
        f"Сейчас в анкете: <b>{media_count}/3</b> фото\n\n"
        "Что хочешь сделать?",
        parse_mode="HTML",
        reply_markup=get_photo_edit_keyboard()
    )


async def upload_new_photos(message: types.Message, state: FSMContext):
    await message.answer(
        "📷 <b>Загрузка новых фото</b>\n\n"
        "Отправляй новые фото (до 3 штук).\n"
        "Старые фото будут <b>полностью заменены</b> новыми.\n\n"
        "Когда закончишь, нажми «✅ Завершить загрузку фото».",
        parse_mode="HTML",
        reply_markup=get_photo_upload_keyboard()
    )
    
    await state.update_data(new_media=[])
    await state.set_state(ProfileStates.waiting_for_new_photos)


async def keep_current_photos(message: types.Message, state: FSMContext):
    await message.answer(
        "✅ Текущие фото сохранены.",
        reply_markup=hide_keyboard()
    )
    await return_to_edit_menu(message, state)


@router.message(ProfileStates.waiting_for_new_photos)
async def process_new_photos(message: types.Message, state: FSMContext):
    if message.text == "🔙 Отмена":
        await return_to_edit_menu(message, state)
        return
    
    if message.text == "✅ Завершить загрузку фото":
        await finish_photos_upload(message, state)
        return
    
    if message.photo:
        file_id = message.photo[-1].file_id
        media_type = "photo"
    elif message.document and message.document.mime_type.startswith('image/'):
        file_id = message.document.file_id
        media_type = "photo"
    elif message.video:
        file_id = message.video.file_id
        media_type = "video"
    else:
        await message.answer("⚠️ Пожалуйста, отправь фото, видео или нажми «✅ Завершить загрузку фото».")
        return
    
    data = await state.get_data()
    new_media = data.get("new_media", [])
    
    if len(new_media) >= 3:
        await message.answer(
            "⚠️ Достигнут лимит в 3 фото.\n"
            "Нажми «✅ Завершить загрузку фото» для сохранения."
        )
        return
    
    new_media.append({"file_id": file_id, "type": media_type})
    await state.update_data(new_media=new_media)
    
    media_names = {
        'photo': 'Фото',
        'video': 'Видео'
    }
    
    await message.answer(
        f"✅ {media_names[media_type]} добавлено! ({len(new_media)}/3)\n"
        "Отправляй ещё или нажми «✅ Завершить загрузку фото»."
    )


async def finish_photos_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_media = data.get("new_media", [])
    
    if not new_media:
        await message.answer(
            "⚠️ Ты не загрузил ни одного фото.\n"
            "Хочешь оставить старые фото?",
            reply_markup=get_photo_edit_keyboard()
        )
        await state.set_state(ProfileStates.editing_profile)
        return
    
    telegram_id = message.from_user.id
    try:
        await backend_client.update_profile(telegram_id, {"media": new_media})
        
        profile = data.get('original_profile', {})
        profile['media'] = new_media
        await state.update_data(original_profile=profile)
        
        await message.answer(
            f"✅ Фото обновлены! Загружено: {len(new_media)}/3",
            reply_markup=hide_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error updating photos: {e}")
        await message.answer("❌ Ошибка при обновлении фото. Попробуй позже.")
    
    await return_to_edit_menu(message, state)


@router.message(F.text == "Скрыть анкету")
async def delete_profile_start(message: types.Message, state: FSMContext):
    await message.answer(
        "⚠️ <b>Скрытие анкеты</b>\n\n"
        "Точно хочешь скрыть анкету?",
        parse_mode="HTML",
        reply_markup=get_confirmation_keyboard("✅ Да, скрыть", "❌ Нет, отмена")
    )
    await state.set_state(ProfileStates.waiting_for_delete_confirm)


@router.message(ProfileStates.waiting_for_delete_confirm, F.text == "✅ Да, скрыть")
async def confirm_delete(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    try:
        await backend_client.update_profile(telegram_id, {"is_active": False})
        await message.answer(
            "Анкета скрыта.\n\nЕсли захочешь вернуться напиши мне",
            reply_markup=return_my_profile_active()
        )
    except Exception as e:
        logger.error(f"Error deleting profile: {e}")
        await message.answer("⚠️ Ошибка при удалении")
    finally:
        await state.clear()


@router.message(ProfileStates.waiting_for_delete_confirm, F.text == "❌ Нет, отмена")
async def cancel_delete(message: types.Message, state: FSMContext):
    await state.clear()
    from src.handlers.profile import show_my_profile_message
    await show_my_profile_message(message, message.from_user.id)


@router.message(F.text == "Вернуться назад")
async def user_come_back(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    first_name = message.from_user.first_name

    await state.clear()
    
    profile = await backend_client.get_profile(telegram_id)
    if not profile:
        await message.answer(
            "⚠️ Сначала создайте анкету!",
            reply_markup=get_main_menu_keyboard(has_profile=False)
        )
        return
    
    await backend_client.update_profile(telegram_id, {"is_active": True})

    await message.answer(
        f"👋 Привет, {first_name}!\n\n"
        f"Рад тебя снова видеть, давай искать GYM Bro 💪",
        reply_markup=get_main_menu_keyboard(has_profile=True)
    )

async def return_to_edit_menu(message: types.Message, state: FSMContext):
    data = await state.get_data()
    profile = data.get('original_profile', {})
    
    try:
        updated_profile = await backend_client.get_profile(message.from_user.id)
        if updated_profile:
            await state.update_data(original_profile=updated_profile)
            profile = updated_profile
    except:
        pass
    
    await message.answer(
        "✏️ <b>Редактирование анкеты</b>\n\n"
        "Выбери, что хочешь изменить:\n\n"
        f"👤 Имя: <b>{profile.get('name', 'Не указано')}</b>\n"
        f"🎂 Возраст: <b>{profile.get('age', 'Не указан')}</b>\n"
        f"💪 Опыт: <b>{_extract_experience(profile.get('description', ''))}</b>\n"
        f"📷 Фото: <b>{len(profile.get('media', []))}/3</b>",
        parse_mode="HTML",
        reply_markup=get_edit_choice_keyboard()
    )
    await state.set_state(ProfileStates.editing_profile)


async def finish_editing(message: types.Message, state: FSMContext):
    await state.clear()
    from src.handlers.profile import show_my_profile_message
    await show_my_profile_message(message, message.from_user.id)