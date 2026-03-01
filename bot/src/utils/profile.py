import logging
from typing import List, Dict
from aiogram import types
from aiogram.utils.media_group import MediaGroupBuilder

logger = logging.getLogger(__name__)

async def _send_profile_album(
    message: types.Message,
    media_list: List[Dict[str, str]],
    caption: str,
    reply_markup=None,
    parse_mode: str = "HTML"
):    
    if not media_list:
        await message.answer(caption, reply_markup=reply_markup, parse_mode=parse_mode)
        return
    
    try:
        album_builder = MediaGroupBuilder(caption=caption)
        valid_items = 0
        
        for media_item in media_list[:10]:
            media_type = media_item.get("type", "photo")
            file_id = media_item["file_id"]
            
            try:
                if media_type == "photo":
                    album_builder.add_photo(media=file_id)
                elif media_type == "video":
                    album_builder.add_video(media=file_id)
                valid_items += 1
            except:
                logger.warning(f"Skipping invalid {media_type} with file_id {file_id}: {e}")
                continue
        
        album = album_builder.build()
        
        if album:
            await message.answer_media_group(media=album)
            logger.info(f"Album sent: {len(album)} items, keyboard attached")
            return
        else:
            logger.warning("No valid media items to send in album")
            
    except Exception as e:
        logger.error(f"Media group failed: {e}")
    
    await message.answer(caption, reply_markup=reply_markup, parse_mode=parse_mode)

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

def _format_profile_text(profile: dict) -> str:
    gender_text = "👨 Парень" if profile['gender'] == 'male' else "👩 Девушка"
    status_text = "✅ Активна" if profile['is_active'] else "⏸ Скрыта"
    
    description = profile['description']
    name = profile['name']
    age = profile['age']
    
    text = (
        f"👤 <b>{name}</b>, {age} лет\n\n"
        f"{description}\n\n"
        f"{gender_text}\n"
        f"{status_text}"
    )
    return text
