import asyncio
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
from src.core.logger import get_service_logger
import secrets
import uuid


class AdminService:
    def __init__(self, session: AsyncSession):
        self.__user_repo = UserRepository(session)
        self.__profile_repo = ProfileRepository(session)
        self.__admin_repo = AdminRepository(session)
        self.logger = get_service_logger()
        self.logger.debug(
            "AdminService initialized",
            extra={"operation": "init"}
        )

    async def _ensure_permissions(self, user: User):
        self.logger.debug(
            "Checking admin permissions",
            extra={
                "operation": "_ensure_permissions",
                "user_id": user.id if user else None,
                "telegram_id": user.telegram_id if user else None
            }
        )
        
        if not secrets.compare_digest(
            str(user.telegram_id),
            str(settings.ADMIN_TELEGRAM_ID)
        ):
            self.logger.warning(
                "Permission denied: user is not admin",
                extra={
                    "operation": "_ensure_permissions",
                    "user_id": user.id if user else None,
                    "telegram_id": user.telegram_id if user else None,
                    "required_telegram_id": settings.ADMIN_TELEGRAM_ID
                }
            )
            raise InvalidPermissions()
        
        self.logger.debug(
            "Admin permissions granted",
            extra={
                "operation": "_ensure_permissions",
                "user_id": user.id if user else None
            }
        )

    async def ban_user(self, user_id: int, admin: User):
        self.logger.info(
            "Ban user requested",
            extra={
                "operation": "ban_user",
                "admin_id": admin.id,
                "target_user_id": user_id
            }
        )
        
        try:
            await self._ensure_permissions(admin)
            
            user = await self.__user_repo.get(user_id)
            if not user:
                self.logger.warning(
                    "User not found for ban",
                    extra={
                        "operation": "ban_user",
                        "target_user_id": user_id
                    }
                )
                raise UserNotFound()
            
            if user.id == admin.id:
                self.logger.warning(
                    "Admin attempted to ban themselves",
                    extra={
                        "operation": "ban_user",
                        "admin_id": admin.id
                    }
                )
                raise InvalidPermissions()

            await self.__user_repo.update(user, is_banned=True)
            self.logger.info(
                "User banned successfully",
                extra={
                    "operation": "ban_user",
                    "user_id": user.id,
                    "telegram_id": user.telegram_id
                }
            )
            
            profile = await self.__profile_repo.get_by_user_id(user_id)
            if profile:
                await self.__profile_repo.delete(profile)
                await cache.invalidate_profile(profile.id)
                self.logger.debug(
                    "User profile deleted",
                    extra={
                        "operation": "ban_user",
                        "user_id": user_id,
                        "profile_id": profile.id
                    }
                )
            
        except (UserNotFound, InvalidPermissions):
            raise
        except Exception as e:
            self.logger.error(
                "Failed to ban user",
                extra={
                    "operation": "ban_user",
                    "target_user_id": user_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def export_profiles_to_csv(
        self,
        admin: User,
        limit: int = 1000,
        offset: int = 0,
        is_active: Optional[bool] = None,
    ) -> str:
        self.logger.info(
            "Export profiles to CSV requested",
            extra={
                "operation": "export_profiles_to_csv",
                "admin_id": admin.id,
                "limit": limit,
                "offset": offset,
                "is_active": is_active
            }
        )
        
        try:
            await self._ensure_permissions(admin)
            
            csv_data = await self.__admin_repo.export_profiles_to_csv(
                limit,
                offset,
                is_active
            )
            
            self.logger.info(
                "Profiles exported successfully",
                extra={
                    "operation": "export_profiles_to_csv",
                    "admin_id": admin.id,
                    "csv_size_bytes": len(csv_data),
                    "estimated_rows": csv_data.count('\n') - 1
                }
            )
            
            return csv_data
            
        except InvalidPermissions:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to export profiles",
                extra={
                    "operation": "export_profiles_to_csv",
                    "admin_id": admin.id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    async def run_broadcast_task(
        self,
        admin: User,
        admin_chat_id: int,
        message_text: str,
        batch_size: int = 50,
        delay_between: float = 1.0,
    ):
        self.logger.info(
            "Broadcast task requested",
            extra={
                "operation": "run_broadcast_task",
                "admin_id": admin.id,
                "admin_chat_id": admin_chat_id,
                "message_length": len(message_text),
                "batch_size": batch_size,
                "delay_between": delay_between
            }
        )
        
        try:
            await self._ensure_permissions(admin)
            
            task_id = str(uuid.uuid4())[:8]
            self.logger.info(
                f"Broadcast task started",
                extra={
                    "operation": "run_broadcast_task",
                    "task_id": task_id,
                    "admin_id": admin.id
                }
            )
            
            stats = {
                "total": 0,
                "sent": 0,
                "failed": 0,
                "blocked": 0,
            }
            
            offset = 0
            batch_num = 1
            
            while True:
                self.logger.debug(
                    f"Processing batch {batch_num}",
                    extra={
                        "operation": "run_broadcast_task",
                        "task_id": task_id,
                        "batch_number": batch_num,
                        "offset": offset,
                        "batch_size": batch_size
                    }
                )
                
                users = await self.__user_repo.get_active_telegram_ids(
                    limit=batch_size,
                    offset=offset
                )
                
                if not users:
                    self.logger.debug(
                        "No more users to process",
                        extra={
                            "operation": "run_broadcast_task",
                            "task_id": task_id,
                            "batch_number": batch_num
                        }
                    )
                    break
                
                for user in users:
                    telegram_id = user[0]
                    stats["total"] += 1
                                    
                    try:
                        success = await telegram_service.send_message(
                            chat_id=telegram_id,
                            text=message_text,
                            parse_mode="HTML"
                        )
                        
                        if success:
                            stats["sent"] += 1
                            self.logger.debug(
                                f"Message sent to {telegram_id}",
                                extra={
                                    "operation": "run_broadcast_task",
                                    "task_id": task_id,
                                    "telegram_id": telegram_id,
                                    "status": "sent"
                                }
                            )
                        else:
                            if "bot was blocked" in str(stats.get("last_error", "")).lower():
                                stats["blocked"] += 1
                                status = "blocked"
                            else:
                                stats["failed"] += 1
                                status = "failed"
                            
                            self.logger.warning(
                                f"Failed to send to {telegram_id}",
                                extra={
                                    "operation": "run_broadcast_task",
                                    "task_id": task_id,
                                    "telegram_id": telegram_id,
                                    "status": status
                                }
                            )
                                
                    except Exception as e:
                        stats["failed"] += 1
                        error_msg = str(e).lower()
                        if "blocked" in error_msg or "forbidden" in error_msg:
                            stats["blocked"] += 1
                            status = "blocked"
                        else:
                            status = "error"
                        
                        self.logger.warning(
                            f"Exception sending to {telegram_id}",
                            extra={
                                "operation": "run_broadcast_task",
                                "task_id": task_id,
                                "telegram_id": telegram_id,
                                "status": status,
                                "error": str(e)
                            }
                        )
                    
                    await asyncio.sleep(0.1)
                
                offset += batch_size
                batch_num += 1
                
                self.logger.info(
                    f"Batch {batch_num-1} completed",
                    extra={
                        "operation": "run_broadcast_task",
                        "task_id": task_id,
                        "batch_number": batch_num-1,
                        "current_stats": stats
                    }
                )
                
                if users:
                    await asyncio.sleep(delay_between)
            
            await self._send_broadcast_stats_to_admin(
                admin_chat_id=admin_chat_id,
                task_id=task_id,
                stats=stats,
                message_preview=message_text[:100]
            )
            
            self.logger.info(
                f"Broadcast task completed",
                extra={
                    "operation": "run_broadcast_task",
                    "task_id": task_id,
                    "admin_id": admin.id,
                    "final_stats": stats
                }
            )

        except InvalidPermissions:
            raise
        except Exception as e:
            self.logger.error(
                "Broadcast task failed",
                extra={
                    "operation": "run_broadcast_task",
                    "admin_id": admin.id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    async def _send_broadcast_stats_to_admin(
        self,
        admin_chat_id: int,
        task_id: str,
        stats: dict,
        message_preview: str
    ):
        self.logger.debug(
            "Sending broadcast stats to admin",
            extra={
                "operation": "_send_broadcast_stats_to_admin",
                "admin_chat_id": admin_chat_id,
                "task_id": task_id,
                "stats": stats
            }
        )
        
        try:
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
            )
            
            await telegram_service.send_message(
                chat_id=admin_chat_id,
                text=text,
                parse_mode="HTML"
            )
            
            self.logger.debug(
                "Broadcast stats sent to admin",
                extra={
                    "operation": "_send_broadcast_stats_to_admin",
                    "admin_chat_id": admin_chat_id,
                    "task_id": task_id
                }
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to send broadcast stats to admin",
                extra={
                    "operation": "_send_broadcast_stats_to_admin",
                    "admin_chat_id": admin_chat_id,
                    "task_id": task_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )