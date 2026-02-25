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
        await message.answer(
            caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return
    
    try:
        album_builder = MediaGroupBuilder(caption=caption)
        
        for media_item in media_list[:10]:
            media_type = media_item.get("type", "photo")
            file_id = media_item["file_id"]
            
            if media_type == "photo":
                album_builder.add_photo(media=file_id)
            elif media_type == "video":
                album_builder.add_video(media=file_id)
        
        album = album_builder.build()
        
        if album:
            sent_messages = await message.answer_media_group(media=album)
            
            if reply_markup and sent_messages:
                await sent_messages[-1].edit_reply_markup(reply_markup=reply_markup)
                            
            logger.info(f"Album sent: {len(album)} items, keyboard attached")
            return
    except Exception as e:
        logger.error(f"Media group failed: {e}")
    
    try:
        first = media_list[0]
        if first.get("type") == "video":
            await message.answer_video(
                video=first["file_id"],
                caption=caption,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return
        else:
            await message.answer_photo(
                photo=first["file_id"],
                caption=caption,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return
    except Exception as e2:
        logger.error(f"Fallback failed: {e2}")
        await message.answer(
            caption,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        return
    