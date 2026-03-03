import logging
import httpx
from typing import Optional
from src.core.config import settings

logger = logging.getLogger(__name__)


class TelegramNotificationService:
    def __init__(self, bot_token: str):
        self.__bot_token = bot_token
        self.__base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: dict = None
    ) -> bool:
        if not self.__bot_token:
            logger.warning("Telegram bot token not configured, skipping notification")
            return False
        
        url = f"{self.__base_url}/sendMessage"
        payload = {
            "chat_id": str(chat_id),
            "text": text,
            "parse_mode": parse_mode,
        }
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    logger.info(f"✅ Notification sent to chat {chat_id}")
                    return True
                else:
                    logger.error(
                        f"❌ Failed to send notification to {chat_id}: "
                        f"{response.status_code} - {response.text}"
                    )
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error sending notification to {chat_id}: {e}")
            return False
    
    async def notify_new_like(
        self,
        chat_id: int | str,
    ) -> bool:        
        text = (
            f"❤️ <b>Вам поставили лайк!</b>\n"
            f"Зайдите в бота, чтобы посмотреть анкету! 👀"
        )
        
        reply_markup = {
            "inline_keyboard": [
                [{"text": "👤 Посмотреть анкету", "callback_data": "check_incoming"}]
            ]
        }
        
        return await self.send_message(chat_id, text, reply_markup=reply_markup)
    
    async def notify_new_match(
        self,
        chat_id: int | str,
        matched_username: Optional[str] = None,
        matched_name: Optional[str] = None
    ) -> bool:
        sender = f"@{matched_username}" if matched_username else (matched_name or "Пользователь")
        
        text = (
            f"🎉 <b>А вот и твой возможный GYM Bro!</b>\n\n"
            f"{sender}\n\n"
            f"Теперь вы можете написать друг другу!"
        )
                
        return await self.send_message(chat_id, text)
    
    async def send_media_group(
        self,
        chat_id: int | str,
        media_items: list[dict],
        caption: str = None,
        parse_mode: str = "HTML"
    ) -> bool:
        if not self.__bot_token or not media_items:
            return False
        
        url = f"{self.__base_url}/sendMediaGroup"
        
        media_payload = []
        for i, item in enumerate(media_items[:10]):
            media_obj = {
                "type": item["type"],
                "media": item["media"],
            }
            if i == 0 and caption:
                media_obj["caption"] = caption
                media_obj["parse_mode"] = parse_mode
            
            media_payload.append(media_obj)
        
        payload = {
            "chat_id": str(chat_id),
            "media": media_payload,
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                
                if response.status_code == 200:
                    logger.info(f"✅ Media group sent to {chat_id}")
                    return True
                else:
                    logger.error(f"❌ Failed to send media group: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error sending media group to {chat_id}: {e}")
            return False

telegram_service = TelegramNotificationService(settings.TELEGRAM_BOT_TOKEN)