from src.models.profile import Profile
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions.profile import NoMoreProfilesException
from src.repositories.profile import ProfileRepository
from src.repositories.user import UserRepository
from src.repositories.action import ActionRepository
from src.repositories.match import MatchRepository
from src.models.action import ActionTypeEnum
from src.core.exceptions.action import SelfActionException
from src.services.telegram import telegram_service
from src.services.cache import cache
from src.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ActionService:
    def __init__(self, session: AsyncSession):
        self.__user_repo = UserRepository(session)
        self.__action_repo = ActionRepository(session)
        self.__match_repo = MatchRepository(session)
        self.__profile_repo = ProfileRepository(session)

    async def _send_like_notification(self, to_user_id: int):
        to_user = await self.__user_repo.get(to_user_id)
        
        if not to_user or not to_user.telegram_id:
            return
        
        await telegram_service.notify_new_like(
            chat_id=to_user.telegram_id,
        )
                
    async def _send_match_notification(self, user1_id: int, user2_id: int):
        user1 = await self.__user_repo.get(user1_id)
        user2 = await self.__user_repo.get(user2_id)
        
        if user1 and user1.telegram_id:
            await telegram_service.notify_new_match(
                chat_id=user1.telegram_id,
                matched_username=user2.username if user2 else None,
                matched_name=user2.first_name if user2 else None
            )
        
        if user2 and user2.telegram_id:
            await telegram_service.notify_new_match(
                chat_id=user2.telegram_id,
                matched_username=user1.username if user1 else None,
                matched_name=user1.first_name if user1 else None
            )
    
    async def _send_report_notification_to_admin(
        self, 
        from_user_id: int,
        to_user_id: int,
        report_reason: str
    ):
        profile = await self.__profile_repo.get_by_user_id(to_user_id)
        reported_user = await self.__user_repo.get(to_user_id)
        reporter_user = await self.__user_repo.get(from_user_id)
        
        if not profile or not reported_user:
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
        else:
            await telegram_service.send_message(
                chat_id=settings.ADMIN_TELEGRAM_ID,
                text=caption,
                parse_mode="HTML"
            )

    async def send_action(
        self, 
        from_user_id: int, 
        to_user_id: int, 
        action_type: ActionTypeEnum,
        report_reason: str = None
    ) -> dict:
        if from_user_id == to_user_id:
            raise SelfActionException()
                
        await self.__action_repo.create(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            action_type=action_type.value.lower(),
            report_reason=report_reason if action_type == ActionTypeEnum.report else None
        )
        
        await cache.add_seen_user_id(from_user_id, to_user_id)
        await cache.add_seen_user_id(to_user_id, from_user_id)

        if action_type == ActionTypeEnum.like:
            is_match = await self.__action_repo.check_mutual_like(from_user_id, to_user_id)
            
            if is_match:
                await self.__match_repo.create_match(from_user_id, to_user_id)
                await self._send_match_notification(from_user_id, to_user_id)
            else:
                await self._send_like_notification(to_user_id)
        elif action_type == ActionTypeEnum.report and report_reason:
            await self._send_report_notification_to_admin(
                from_user_id,
                to_user_id,
                report_reason
            )

    async def decide_on_incoming(
        self, 
        viewer_user_id: int, 
        target_user_id: int, 
        action_type: ActionTypeEnum
    ) -> dict:
        if viewer_user_id == target_user_id:
            raise SelfActionException()
        
        await self.__action_repo.create(
            from_user_id=viewer_user_id,
            to_user_id=target_user_id,
            action_type=action_type
        )
        
        await cache.add_seen_user_id(viewer_user_id, target_user_id)
        
        if action_type == ActionTypeEnum.like:
            await self.__match_repo.create_match(viewer_user_id, target_user_id)
            await self._send_match_notification(viewer_user_id, target_user_id)
    
    async def get_next_incoming_like(self, user_id: int) -> dict:
        incoming_actions = await self.__action_repo.get_incoming_likes(user_id)
        
        if not incoming_actions:
            raise NoMoreProfilesException()
        
        for action in incoming_actions:
            profile = await self.__profile_repo.get_by_user_id(action.from_user_id)
            if profile and profile.is_active:
                return profile
        
        raise NoMoreProfilesException()