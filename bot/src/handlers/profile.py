import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from src.api.client import backend_client
from src.keyboards.main_menu import get_main_menu_keyboard
from src.keyboards.profile import (
    get_profile_actions_keyboard,
    get_gender_keyboard,
    get_experience_keyboard,
    get_name_keyboard,
    get_photo_upload_keyboard,
    get_cancel_keyboard,
    hide_keyboard
)
from src.utils.profile import _format_profile_text, _send_profile_album
from src.states.profile import ProfileStates

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "create_profile")
async def start_create_profile(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    await callback.message.edit_text(
        "📝 <b>Создание анкеты</b>\n\n"
        "👋 <b>Шаг 1 из 6</b>\n\n"
        "Как тебя зовут?",
        parse_mode="HTML"
    )
    await state.set_state(ProfileStates.waiting_for_name)


async def start_create_profile_from_menu(
    message: types.Message,
    first_name: str,
    state: FSMContext
):
    await state.clear()
    
    await message.answer(
        "📝 <b>Создание анкеты</b>\n\n"
        "👋 <b>Шаг 1 из 6</b>\n\n"
        "Как тебя зовут?",
        parse_mode="HTML",
        reply_markup=get_name_keyboard(first_name)
    )
    await state.set_state(ProfileStates.waiting_for_name)


@router.message(ProfileStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):    
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("⚠️ Имя слишком короткое. Введи корректное имя:")
        return
    if len(name) > 50:
        await message.answer("⚠️ Имя слишком длинное (максимум 50 символов).")
        return
    
    await state.update_data(name=name)
    
    await message.answer(
        f"✅ Привет, <b>{name}</b>!",
        parse_mode="HTML",
        reply_markup=hide_keyboard()
    )

    await message.answer(
        f"👤 <b>Шаг 2 из 6</b>\n\n"
        "Выбери свой пол:",
        parse_mode="HTML",
        reply_markup=get_gender_keyboard()
    )
    await state.set_state(ProfileStates.waiting_for_gender)


@router.message(ProfileStates.waiting_for_gender, F.text)
async def process_gender(message: types.Message, state: FSMContext):    
    gender_map = {
        "👨 Парень": "male",
        "👩 Девушка": "female"
    }
    
    if message.text not in gender_map:
        await message.answer("⚠️ Пожалуйста, выбери пол из кнопок ниже:")
        return
    
    gender = gender_map[message.text]
    await state.update_data(gender=gender)
    
    await message.answer(
        "✅ Пол сохранён!\n\n"
        f"🎂 <b>Шаг 3 из 6</b>\n\n"
        "Сколько тебе лет?\n\n"
        "<i>Введи число от 16 до 100</i>",
        parse_mode="HTML",
        reply_markup=hide_keyboard()
    )
    await state.set_state(ProfileStates.waiting_for_age)


@router.message(ProfileStates.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):    
    try:
        age = int(message.text.strip())
        if age < 16 or age > 100:
            await message.answer("Введенный возраст неккоректный\nПопробуй ещё раз")
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
        await message.answer("Это не число. Введите возраст цифрами")


@router.message(ProfileStates.waiting_for_experience, F.text)
async def process_experience(message: types.Message, state: FSMContext):    
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
    
    if message.text not in exp_map:
        await message.answer("⚠️ Пожалуйста, выбери уровень опыта из кнопок ниже:")
        return
    
    exp_key = exp_map[message.text]
    experience_text = exp_labels[exp_key]
    
    await state.update_data(experience=experience_text)
    
    await message.answer(
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
        reply_markup=hide_keyboard()
    )
    await state.set_state(ProfileStates.waiting_for_about)


@router.message(ProfileStates.waiting_for_about)
async def process_about(message: types.Message, state: FSMContext):    
    about = message.text.strip()
    
    if len(about) < 10:
        await message.answer("Описание слишком короткое (мин. 10 символов).\nРасскажи о себе подробнее")
        return
    
    data = await state.get_data()
    experience = data.get("experience", "")
    full_description = f"{about}\n\n🏋️ Опыт тренировок: {experience}"
    
    if len(full_description) > 1000:
        await message.answer(f"Описание слишком длинное ({len(full_description)} символов, макс. 1000).\nСократи немного:")
        return
    
    await state.update_data(description=full_description)
    
    await message.answer(
        "✅ Описание сохранено!\n\n"
        f"📷 <b>Шаг 6 из 6</b>\n\n"
        "Отправь фото или видео для анкеты (до 3 файлов).\n"
        "Это необязательно, но с фото анкета выглядит лучше!\n\n"
        "Когда закончишь — нажми «✅ Завершить загрузку фото».",
        parse_mode="HTML",
        reply_markup=get_photo_upload_keyboard()
    )
    await state.set_state(ProfileStates.waiting_for_photo)


@router.message(ProfileStates.waiting_for_photo)
async def process_photo(message: types.Message, state: FSMContext):    
    if message.text == "✅ Завершить загрузку фото":
        await finish_photo_upload(message, state)
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
        await message.answer("Пожалуйста, отправь фото, видео или нажми «✅ Завершить загрузку фото».")
        return
    
    data = await state.get_data()
    media_list = data.get("media", [])
    
    if len(media_list) >= 3:
        await message.answer(
            "⚠️ Максимум 3 медиафайла в анкете.\n"
            "Нажми «✅ Завершить загрузку фото» для завершения."
        )
        return
    
    media_list.append({"file_id": file_id, "type": media_type})
    await state.update_data(media=media_list)

    media_names = {
        'photo': 'Фото',
        'video': 'Видео'
    }
    
    await message.answer(
        f"✅ {media_names[media_type]} добавлено! ({len(media_list)}/3)\n"
        "Отправляй ещё или нажми «✅ Завершить загрузку фото»."
    )


async def finish_photo_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    telegram_id = message.from_user.id
    
    profile_data = {
        "name": data.get("name"),
        "description": data.get("description"),
        "gender": data.get("gender"),
        "age": data.get("age"),
        "media": data.get("media", [])
    }
    
    logger.info(f"Creating profile for user {telegram_id}")
    
    await backend_client.create_profile(telegram_id, profile_data)
    
    await state.clear()
    
    await message.answer(
        "🎉 <b>Анкета создана!</b>\n\n"
        "Теперь ты можешь искать партнёров для тренировок.\n"
        "Нажми «🔍 Начать свайпать», чтобы увидеть анкеты!",
        reply_markup=get_main_menu_keyboard(has_profile=True),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "my_profile")
async def show_my_profile(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id
    profile = await backend_client.get_profile(telegram_id)
    
    if not profile:
        await callback.message.edit_text(
            "У вас нет анкеты. Создайте её!",
            reply_markup=get_main_menu_keyboard(has_profile=False)
        )
        return
    
    await callback.message.answer(
        "👤 <b>Управление анкетой</b>",
        parse_mode="HTML",
        reply_markup=get_profile_actions_keyboard()
    )
    
    await _send_profile_album(
        message=callback.message,
        media_list=profile.get('media', []),
        caption=_format_profile_text(profile),
        reply_markup=None
    )
    

async def show_my_profile_message(message: types.Message, telegram_id: int):
    profile = await backend_client.get_profile(telegram_id)
    
    if not profile:
        await message.answer("У вас нет анкеты. Создайте её!", reply_markup=get_main_menu_keyboard(has_profile=False))
        return
    
    await message.answer(
        "👤 <b>Управление анкетой</b>",
        parse_mode="HTML",
        reply_markup=get_profile_actions_keyboard()
    )

    await _send_profile_album(
        message=message,
        media_list=profile.get('media', []),
        caption=_format_profile_text(profile),
        reply_markup=None
    )
    

@router.message(F.text == "🔙 Вернуться в главное меню")
async def back_to_main_from_profile(message: types.Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    profile = await backend_client.get_profile(telegram_id)
    
    await message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_menu_keyboard(has_profile=bool(profile))
    )

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
