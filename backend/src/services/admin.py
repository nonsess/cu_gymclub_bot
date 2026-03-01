import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.admin import AdminRepository
from src.core.exceptions.user import UserNotFound
from src.core.exceptions.admin import InvalidPermissions
from src.models.user import User
from src.repositories.profile import ProfileRepository
from src.repositories.user import UserRepository
from src.services.cache import cache
from src.services.telegram import telegram_service
from src.core.config import settings
import secrets
import uuid

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, session: AsyncSession):
        self.__user_repo = UserRepository(session)
        self.__profile_repo = ProfileRepository(session)
        self.__admin_repo = AdminRepository(session)

    async def _ensure_permissions(self, user: User):
        if not secrets.compare_digest(
            str(user.telegram_id),
            str(settings.ADMIN_TELEGRAM_ID)
        ):
            raise InvalidPermissions()

    async def ban_user(self, user_id: int, admin: User):
        await self._ensure_permissions(admin)
        user = await self.__user_repo.get(user_id)
        if not user:
            raise UserNotFound()
        await self.__user_repo.update(user, is_banned=True)
        
        profile = await self.__profile_repo.get_by_user_id(user_id)
        if profile:
            await self.__profile_repo.update(profile, is_active=False)        
            await cache.invalidate_profile(profile.id)
    
    async def export_profiles_to_csv(
        self,
        admin: User,
        limit: int = 1000,
        offset: int = 0,
        is_active: Optional[bool] = None,
    ) -> str:
        await self._ensure_permissions(admin)
        return await self.__admin_repo.export_profiles_to_csv(
            limit,
            offset,
            is_active
        )

    async def run_broadcast_task(
        self,
        admin: User,
        admin_chat_id: int,
        message_text: str,
        batch_size: int = 50,
        delay_between: float = 1.0,
    ):
        self._ensure_permissions(admin)
        
        task_id = str(uuid.uuid4())[:8]
        logger.info(f"📢 [{task_id}] Broadcast task started")
        
        stats = {
            "total": 0,
            "sent": 0,
            "failed": 0,
            "blocked": 0,
            "no_chat_id": 0,
        }
        
        offset = 0
        
        while True:
            users = await self.__user_repo.get_active_telegram_ids(
                limit=batch_size,
                offset=offset
            )
            
            if not users:
                break
            
            for telegram_id, chat_id in users:
                stats["total"] += 1
                
                if not chat_id:
                    stats["no_chat_id"] += 1
                    continue
                
                try:
                    success = await telegram_service.send_message(
                        chat_id=chat_id,
                        text=message_text,
                        parse_mode="HTML"
                    )
                    
                    if success:
                        stats["sent"] += 1
                    else:
                        if "bot was blocked" in str(stats.get("last_error", "")).lower():
                            stats["blocked"] += 1
                        else:
                            stats["failed"] += 1
                            
                except Exception as e:
                    stats["failed"] += 1
                    error_msg = str(e).lower()
                    if "blocked" in error_msg or "forbidden" in error_msg:
                        stats["blocked"] += 1
                    logger.warning(f"❌ [{task_id}] Failed to {telegram_id}: {e}")
                
                await asyncio.sleep(0.1)
            
            offset += batch_size
            await asyncio.sleep(delay_between)
        
        await self._send_broadcast_stats_to_admin(
            admin_chat_id=admin_chat_id,
            task_id=task_id,
            stats=stats,
            message_preview=message_text[:100]
        )
        
        logger.info(f"📢 [{task_id}] Broadcast completed: {stats}")

    async def _send_broadcast_stats_to_admin(
        self,
        admin_chat_id: int,
        task_id: str,
        stats: dict,
        message_preview: str
    ):
        success_rate = (stats["sent"] / stats["total"] * 100) if stats["total"] > 0 else 0
        
        text = (
            f"✅ <b>Рассылка завершена</b>\n\n"
            f"🆔 Задача: <code>{task_id}</code>\n"
            f"📝 Сообщение: <i>{message_preview}...</i>\n\n"
            f"📊 <b>Статистика:</b>\n"
            f"• Всего пользователей: {stats['total']}\n"
            f"• ✅ Доставлено: {stats['sent']} ({success_rate:.1f}%)\n"
            f"• ❌ Ошибки: {stats['failed']}\n"
            f"• 🚫 Заблокировали бота: {stats['blocked']}\n"
            f"• ⚠️ Нет chat_id: {stats['no_chat_id']}\n\n"
        )
        
        await telegram_service.send_message(
            chat_id=admin_chat_id,
            text=text,
            parse_mode="HTML"
        )
