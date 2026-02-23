import logging
import httpx
from typing import Optional
from src.core.config import settings

logger = logging.getLogger(__name__)


class TelegramNotificationService:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: dict = None
    ) -> bool:
        if not self.bot_token:
            logger.warning("Telegram bot token not configured, skipping notification")
            return False
        
        url = f"{self.base_url}/sendMessage"
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
        liker_username: Optional[str] = None,
        liker_name: Optional[str] = None
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


telegram_service = TelegramNotificationService(settings.TELEGRAM_BOT_TOKEN)