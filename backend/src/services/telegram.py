import httpx
from typing import Optional
from src.core.config import settings
from src.core.logger import get_service_logger

class TelegramNotificationService:
    def __init__(self, bot_token: str):
        self.__bot_token = bot_token
        self.__base_url = f"https://api.telegram.org/bot{bot_token}"
        self.logger = get_service_logger()
        self.logger.debug(
            "TelegramNotificationService initialized",
            extra={
                "operation": "init",
                "has_bot_token": bool(bot_token)
            }
        )
    
    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: dict = None
    ) -> bool:
        self.logger.debug(
            "Sending message",
            extra={
                "operation": "send_message",
                "chat_id": str(chat_id),
                "text_length": len(text),
                "parse_mode": parse_mode,
                "has_reply_markup": reply_markup is not None
            }
        )
        
        if not self.__bot_token:
            self.logger.warning(
                "Telegram bot token not configured, skipping notification",
                extra={
                    "operation": "send_message",
                    "chat_id": str(chat_id)
                }
            )
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
                    self.logger.info(
                        f"Message sent to chat {chat_id}",
                        extra={
                            "operation": "send_message",
                            "chat_id": str(chat_id),
                            "status": "success",
                            "status_code": response.status_code
                        }
                    )
                    return True
                else:
                    self.logger.error(
                        f"Failed to send message to {chat_id}",
                        extra={
                            "operation": "send_message",
                            "chat_id": str(chat_id),
                            "status_code": response.status_code,
                            "response": response.text[:200] if response.text else None
                        }
                    )
                    return False
                    
        except httpx.TimeoutException as e:
            self.logger.error(
                f"Timeout sending message to {chat_id}",
                extra={
                    "operation": "send_message",
                    "chat_id": str(chat_id),
                    "error_type": "TimeoutException",
                    "error": str(e)
                }
            )
            return False
        except Exception as e:
            self.logger.error(
                f"Error sending message to {chat_id}",
                extra={
                    "operation": "send_message",
                    "chat_id": str(chat_id),
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            return False
    
    async def notify_new_like(
        self,
        chat_id: int | str,
    ) -> bool:
        self.logger.debug(
            "Sending new like notification",
            extra={
                "operation": "notify_new_like",
                "chat_id": str(chat_id)
            }
        )
        
        text = (
            f"❤️ <b>Вам поставили лайк!</b>\n"
            f"Зайдите в бота, чтобы посмотреть анкету! 👀"
        )
        
        reply_markup = {
            "inline_keyboard": [
                [{"text": "👤 Посмотреть анкету", "callback_data": "check_incoming"}]
            ]
        }
        
        result = await self.send_message(chat_id, text, reply_markup=reply_markup)
        
        if result:
            self.logger.debug(
                "New like notification sent",
                extra={
                    "operation": "notify_new_like",
                    "chat_id": str(chat_id),
                    "status": "sent"
                }
            )
        
        return result
    
    async def notify_new_match(
        self,
        chat_id: int | str,
        matched_username: Optional[str] = None,
        matched_name: Optional[str] = None
    ) -> bool:
        sender = f"@{matched_username}" if matched_username else (matched_name or "Пользователь")
        
        self.logger.info(
            "Sending new match notification",
            extra={
                "operation": "notify_new_match",
                "chat_id": str(chat_id),
                "matched_username": matched_username,
                "matched_name": matched_name,
                "sender": sender
            }
        )
        
        text = (
            f"🎉 <b>А вот и твой возможный GYM Bro!</b>\n\n"
            f"{sender}\n\n"
            f"Теперь вы можете написать друг другу!"
        )
                
        result = await self.send_message(chat_id, text)
        
        if result:
            self.logger.debug(
                "New match notification sent",
                extra={
                    "operation": "notify_new_match",
                    "chat_id": str(chat_id),
                    "status": "sent"
                }
            )
        
        return result
    
    async def send_media_group(
        self,
        chat_id: int | str,
        media_items: list[dict],
        caption: str = None,
        parse_mode: str = "HTML"
    ) -> bool:
        self.logger.debug(
            "Sending media group",
            extra={
                "operation": "send_media_group",
                "chat_id": str(chat_id),
                "media_count": len(media_items),
                "has_caption": caption is not None,
                "caption_length": len(caption) if caption else 0
            }
        )
        
        if not self.__bot_token:
            self.logger.warning(
                "Telegram bot token not configured, skipping media group",
                extra={
                    "operation": "send_media_group",
                    "chat_id": str(chat_id)
                }
            )
            return False
        
        if not media_items:
            self.logger.warning(
                "No media items to send",
                extra={
                    "operation": "send_media_group",
                    "chat_id": str(chat_id)
                }
            )
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
                    self.logger.info(
                        f"Media group sent to {chat_id}",
                        extra={
                            "operation": "send_media_group",
                            "chat_id": str(chat_id),
                            "media_sent": len(media_items[:10]),
                            "status": "success"
                        }
                    )
                    return True
                else:
                    self.logger.error(
                        f"Failed to send media group to {chat_id}",
                        extra={
                            "operation": "send_media_group",
                            "chat_id": str(chat_id),
                            "status_code": response.status_code,
                            "response": response.text[:200] if response.text else None
                        }
                    )
                    return False
                    
        except httpx.TimeoutException as e:
            self.logger.error(
                f"Timeout sending media group to {chat_id}",
                extra={
                    "operation": "send_media_group",
                    "chat_id": str(chat_id),
                    "error_type": "TimeoutException",
                    "error": str(e)
                }
            )
            return False
        except Exception as e:
            self.logger.error(
                f"Error sending media group to {chat_id}",
                extra={
                    "operation": "send_media_group",
                    "chat_id": str(chat_id),
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            return False

telegram_service = TelegramNotificationService(settings.TELEGRAM_BOT_TOKEN)