from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions.profile import NoMoreProfilesException, ProfileNotFoundException
from src.repositories.profile import ProfileRepository
from src.repositories.user import UserRepository
from src.repositories.action import ActionRepository
from src.repositories.match import MatchRepository
from src.models.action import ActionTypeEnum
from src.core.exceptions.action import ActionAlreadyRespondedException, SelfActionException
from src.services.telegram import telegram_service
from src.services.cache import cache
from src.core.config import settings
from src.core.logger import get_service_logger

class ActionService:
    def __init__(self, session: AsyncSession):
        self.__user_repo = UserRepository(session)
        self.__action_repo = ActionRepository(session)
        self.__match_repo = MatchRepository(session)
        self.__profile_repo = ProfileRepository(session)
        self.logger = get_service_logger()
        self.logger.debug(
            "ActionService initialized",
            extra={"operation": "init"}
        )

    async def _send_like_notification(self, to_user_id: int):
        self.logger.debug(
            "Sending like notification",
            extra={
                "operation": "_send_like_notification",
                "to_user_id": to_user_id
            }
        )
        
        try:
            to_user = await self.__user_repo.get(to_user_id)
            
            if not to_user or not to_user.telegram_id:
                self.logger.debug(
                    "User not found or no telegram_id, skipping notification",
                    extra={
                        "operation": "_send_like_notification",
                        "to_user_id": to_user_id,
                        "user_found": to_user is not None,
                        "has_telegram_id": to_user.telegram_id if to_user else None
                    }
                )
                return
            
            await telegram_service.notify_new_like(
                chat_id=to_user.telegram_id,
            )
            
            self.logger.debug(
                "Like notification sent",
                extra={
                    "operation": "_send_like_notification",
                    "to_user_id": to_user_id,
                    "telegram_id": to_user.telegram_id
                }
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to send like notification",
                extra={
                    "operation": "_send_like_notification",
                    "to_user_id": to_user_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
                
    async def _send_match_notification(self, user1_id: int, user2_id: int):
        self.logger.debug(
            "Sending match notifications",
            extra={
                "operation": "_send_match_notification",
                "user1_id": user1_id,
                "user2_id": user2_id
            }
        )
        
        try:
            user1 = await self.__user_repo.get(user1_id)
            user2 = await self.__user_repo.get(user2_id)
            
            if user1 and user1.telegram_id:
                await telegram_service.notify_new_match(
                    chat_id=user1.telegram_id,
                    matched_username=user2.username if user2 else None,
                    matched_name=user2.first_name if user2 else None
                )
                self.logger.debug(
                    "Match notification sent to user1",
                    extra={
                        "operation": "_send_match_notification",
                        "user_id": user1_id,
                        "telegram_id": user1.telegram_id
                    }
                )
            
            if user2 and user2.telegram_id:
                await telegram_service.notify_new_match(
                    chat_id=user2.telegram_id,
                    matched_username=user1.username if user1 else None,
                    matched_name=user1.first_name if user1 else None
                )
                self.logger.debug(
                    "Match notification sent to user2",
                    extra={
                        "operation": "_send_match_notification",
                        "user_id": user2_id,
                        "telegram_id": user2.telegram_id
                    }
                )
                
        except Exception as e:
            self.logger.error(
                "Failed to send match notifications",
                extra={
                    "operation": "_send_match_notification",
                    "user1_id": user1_id,
                    "user2_id": user2_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
    
    async def _send_report_notification_to_admin(
        self, 
        from_user_id: int,
        to_user_id: int,
        report_reason: str
    ):
        self.logger.info(
            "Processing report notification to admin",
            extra={
                "operation": "_send_report_notification_to_admin",
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "report_reason": report_reason
            }
        )
        
        try:
            profile = await self.__profile_repo.get_by_user_id(to_user_id)
            reported_user = await self.__user_repo.get(to_user_id)
            reporter_user = await self.__user_repo.get(from_user_id)
            
            if not profile or not reported_user:
                self.logger.warning(
                    "Profile or reported user not found for report",
                    extra={
                        "operation": "_send_report_notification_to_admin",
                        "from_user_id": from_user_id,
                        "to_user_id": to_user_id,
                        "profile_found": profile is not None,
                        "reported_user_found": reported_user is not None
                    }
                )
                return
            
            gender_map = {
                "male": "👨 Парень",
                "female": "👩 Девушка",
            }
            gender_text = gender_map.get(profile.gender, profile.gender or "❓")
            
            desc_parts = profile.description.split('\n\n🏋️ Опыт тренировок:')
            main_desc = desc_parts[0][:300] + ("..." if len(desc_parts[0]) > 300 else "")
            experience = desc_parts[1] if len(desc_parts) > 1 else None
            
            reporter_name = (
                f"@{reporter_user.username}" if reporter_user and reporter_user.username 
                else f"ID: {reporter_user.telegram_id}" if reporter_user 
                else "Неизвестно"
            )
            reported_name = (
                f"@{reported_user.username}" if reported_user.username 
                else f"ID: {reported_user.telegram_id}"
            )
            
            caption = (
                f"⚠️ <b>НОВАЯ ЖАЛОБА</b>\n\n"
                f"🔍 <b>Информация:</b>\n"
                f"• 📢 Пожаловался: {reporter_name}\n"
                f"• 👤 На пользователя: {reported_name}\n"
                f"• 📋 Причина: {report_reason}\n\n"
                f"📝 <b>Профиль:</b>\n"
                f"• Имя: {profile.name}\n"
                f"• Возраст: {profile.age or '?'}\n"
                f"• Пол: {gender_text}\n"
                f"• Описание: <code>{main_desc}</code>\n"
                f"{f'• Опыт: {experience}\n' if experience else ''}"
                f"• USER_ID: <code>{to_user_id}</code>\n"
                f"• Telegram ID: <code>{reported_user.telegram_id}</code>"
            )
            
            media_payload = []
            
            if profile.media:
                for media in profile.media[:3]:
                    media_payload.append({
                        "type": media.type,
                        "media": media.file_id,
                    })
            
            if media_payload:
                await telegram_service.send_media_group(
                    chat_id=settings.ADMIN_TELEGRAM_ID,
                    media_items=media_payload,
                    caption=caption,
                    parse_mode="HTML"
                )
                self.logger.debug(
                    "Report sent with media",
                    extra={
                        "operation": "_send_report_notification_to_admin",
                        "from_user_id": from_user_id,
                        "to_user_id": to_user_id,
                        "media_count": len(media_payload)
                    }
                )
            else:
                await telegram_service.send_message(
                    chat_id=settings.ADMIN_TELEGRAM_ID,
                    text=caption,
                    parse_mode="HTML"
                )
                self.logger.debug(
                    "Report sent without media",
                    extra={
                        "operation": "_send_report_notification_to_admin",
                        "from_user_id": from_user_id,
                        "to_user_id": to_user_id
                    }
                )
                
        except Exception as e:
            self.logger.error(
                "Failed to send report notification to admin",
                extra={
                    "operation": "_send_report_notification_to_admin",
                    "from_user_id": from_user_id,
                    "to_user_id": to_user_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )

    async def send_action(
        self, 
        from_user_id: int, 
        to_user_id: int, 
        action_type: ActionTypeEnum,
        report_reason: str = None
    ) -> int:
        self.logger.info(
            "Sending action",
            extra={
                "operation": "send_action",
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "action_type": action_type.value if action_type else None,
                "has_report_reason": report_reason is not None
            }
        )
        
        try:
            if from_user_id == to_user_id:
                self.logger.warning(
                    "Self action attempted",
                    extra={
                        "operation": "send_action",
                        "user_id": from_user_id,
                        "action_type": action_type.value if action_type else None
                    }
                )
                raise SelfActionException()
                    
            action = await self.__action_repo.create(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                action_type=action_type.value.lower(),
                report_reason=report_reason if action_type == ActionTypeEnum.report else None
            )
            
            self.logger.debug(
                "Action saved to database",
                extra={
                    "operation": "send_action",
                    "action_id": action.id,
                    "from_user_id": from_user_id,
                    "to_user_id": to_user_id,
                    "action_type": action_type.value if action_type else None
                }
            )
            
            await cache.add_seen_user_id(from_user_id, to_user_id)
            await cache.add_seen_user_id(to_user_id, from_user_id)
            
            self.logger.debug(
                "Users added to seen cache",
                extra={
                    "operation": "send_action",
                    "from_user_id": from_user_id,
                    "to_user_id": to_user_id
                }
            )

            if action_type == ActionTypeEnum.like:
                await self._send_like_notification(to_user_id)                    
            elif action_type == ActionTypeEnum.report and report_reason:
                self.logger.info(
                    "Report action processed",
                    extra={
                        "operation": "send_action",
                        "from_user_id": from_user_id,
                        "to_user_id": to_user_id,
                        "report_reason": report_reason
                    }
                )
                await self._send_report_notification_to_admin(
                    from_user_id,
                    to_user_id,
                    report_reason
                )
            
            return {
                "action_id": action.id,
                "success": True
            }
    
        except SelfActionException:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to send action",
                extra={
                    "operation": "send_action",
                    "from_user_id": from_user_id,
                    "to_user_id": to_user_id,
                    "action_type": action_type.value if action_type else None,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    async def decide_on_incoming(
        self, 
        viewer_user_id: int, 
        action_id: int, 
        decision_type: ActionTypeEnum,
        report_reason: str,
    ) -> dict:
        self.logger.info(
            "Deciding on incoming like",
            extra={
                "operation": "decide_on_incoming",
                "viewer_user_id": viewer_user_id,
                "action_id": action_id,
                "decision_type": decision_type.value if decision_type else None
            }
        )
        
        try:
            incoming_action = await self.__action_repo.get(action_id)
            
            if not incoming_action:
                self.logger.warning(
                    "Incoming action not found",
                    extra={
                        "operation": "decide_on_incoming",
                        "action_id": action_id,
                        "viewer_user_id": viewer_user_id
                    }
                )
                raise ProfileNotFoundException()
            
            if incoming_action.to_user_id != viewer_user_id:
                self.logger.warning(
                    "Action not addressed to this user",
                    extra={
                        "operation": "decide_on_incoming",
                        "action_id": action_id,
                        "viewer_user_id": viewer_user_id,
                        "action_to_user_id": incoming_action.to_user_id
                    }
                )
                raise ProfileNotFoundException()
            
            if incoming_action.action_type != ActionTypeEnum.like:
                self.logger.warning(
                    "Action is not a like",
                    extra={
                        "operation": "decide_on_incoming",
                        "action_id": action_id,
                        "action_type": incoming_action.action_type.value if incoming_action.action_type else None
                    }
                )
                raise NoMoreProfilesException()
            
            if incoming_action.is_responded:
                self.logger.warning(
                    "Action already responded",
                    extra={
                        "operation": "decide_on_incoming",
                        "action_id": action_id,
                        "viewer_user_id": viewer_user_id
                    }
                )
                raise ActionAlreadyRespondedException()
            
            target_user_id = incoming_action.from_user_id
            
            profile_target = await self.__profile_repo.get_by_user_id(target_user_id)
            if not profile_target or not profile_target.is_active:
                raise ProfileNotFoundException()

            await self.__action_repo.mark_as_responded(action_id)
            
            self.logger.debug(
                "Original like marked as responded",
                extra={
                    "operation": "decide_on_incoming",
                    "action_id": action_id
                }
            )

            response_action = await self.__action_repo.create(
                from_user_id=viewer_user_id,
                to_user_id=target_user_id,
                action_type=decision_type,
                report_reason=report_reason if report_reason else ""
            )

            self.logger.debug(
                "Decision saved to database",
                extra={
                    "operation": "decide_on_incoming",
                    "response_action_id": response_action.id,
                    "viewer_user_id": viewer_user_id,
                    "target_user_id": target_user_id,
                    "decision_type": decision_type.value if decision_type else None
                }
            )
            
            await cache.add_seen_user_id(viewer_user_id, target_user_id)
            
            self.logger.debug(
                "User added to seen cache",
                extra={
                    "operation": "decide_on_incoming",
                    "viewer_user_id": viewer_user_id,
                    "target_user_id": target_user_id
                }
            )
            
            result = {"success": True}
            
            if decision_type == ActionTypeEnum.like:
                match = await self.__match_repo.create_match(viewer_user_id, target_user_id)
                self.logger.info(
                    "Match created from incoming decision",
                    extra={
                        "operation": "decide_on_incoming",
                        "match_id": match.id,
                        "user1_id": viewer_user_id,
                        "user2_id": target_user_id
                    }
                )
                await self._send_match_notification(viewer_user_id, target_user_id)
                result["match"] = match
                result["match_id"] = match.id
            
            return result
                
        except (SelfActionException, ProfileNotFoundException, NoMoreProfilesException, ActionAlreadyRespondedException):
            raise
        except Exception as e:
            self.logger.error(
                "Failed to decide on incoming",
                extra={
                    "operation": "decide_on_incoming",
                    "viewer_user_id": viewer_user_id,
                    "action_id": action_id,
                    "decision_type": decision_type.value if decision_type else None,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def get_next_incoming_like(self, user_id: int) -> dict:
        self.logger.debug(
            "Getting next incoming like",
            extra={
                "operation": "get_next_incoming_like",
                "user_id": user_id
            }
        )
        
        try:
            action = await self.__action_repo.get_next_incoming_like(user_id)
            
            if not action:
                self.logger.debug(
                    "No incoming likes found",
                    extra={
                        "operation": "get_next_incoming_like",
                        "user_id": user_id
                    }
                )
                raise NoMoreProfilesException()
            
            profile = await self.__profile_repo.get_by_user_id(action.from_user_id)
            
            if not profile or not profile.is_active:
                self.logger.debug(
                    "Profile is not active, skipping",
                    extra={
                        "operation": "get_next_incoming_like",
                        "user_id": user_id,
                        "from_user_id": action.from_user_id,
                        "profile_id": profile.id if profile else None
                    }
                )
                raise NoMoreProfilesException()
            
            self.logger.debug(
                "Found active profile for incoming like",
                extra={
                    "operation": "get_next_incoming_like",
                    "user_id": user_id,
                    "from_user_id": action.from_user_id,
                    "action_id": action.id,
                    "profile_id": profile.id
                }
            )
            
            return {
                "profile": profile,
                "action_id": action.id
            }
                
        except NoMoreProfilesException:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to get next incoming like",
                extra={
                    "operation": "get_next_incoming_like",
                    "user_id": user_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
