from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions.profile import NoMoreProfilesException
from src.repositories.profile import ProfileRepository
from src.repositories.user import UserRepository
from src.repositories.action import ActionRepository
from src.repositories.match import MatchRepository
from src.models.action import ActionTypeEnum
from src.core.exceptions.action import ActionAlreadyExistsException, SelfActionException
from src.services.telegram import telegram_service

class ActionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.action_repo = ActionRepository(session)
        self.match_repo = MatchRepository(session)
        self.profile_repo = ProfileRepository(session)

    async def _send_like_notification(self, from_user_id: int, to_user_id: int):
        from_user = await self.user_repo.get(from_user_id)
        to_user = await self.user_repo.get(to_user_id)
        
        if not to_user or not to_user.telegram_id:
            return
        
        await telegram_service.notify_new_like(
            chat_id=to_user.telegram_id,
            liker_username=from_user.username if from_user else None,
            liker_name=from_user.first_name if from_user else None
        )
                
    async def _send_match_notification(self, user1_id: int, user2_id: int):
        user1 = await self.user_repo.get(user1_id)
        user2 = await self.user_repo.get(user2_id)
        
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

    async def send_action(
        self, 
        from_user_id: int, 
        to_user_id: int, 
        action_type: ActionTypeEnum,
        report_reason: str = None
    ) -> dict:
        if from_user_id == to_user_id:
            raise SelfActionException()
        
        existing = await self.action_repo.get_action(from_user_id, to_user_id)
        if existing:
            raise ActionAlreadyExistsException(from_user_id, to_user_id)
        
        await self.action_repo.create(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            action_type=action_type.value.lower(),
            report_reason=report_reason if action_type == ActionTypeEnum.report else None
        )
        
        is_match = False
        if action_type == ActionTypeEnum.like:
            is_match = await self.action_repo.check_mutual_like(from_user_id, to_user_id)
            
            if is_match:
                await self.match_repo.create_match(from_user_id, to_user_id)
            else:
                await self._send_like_notification(from_user_id, to_user_id)

        
        return {"is_match": is_match}

    async def get_incoming_likes(self, user_id: int) -> list:
        actions = await self.action_repo.get_incoming_likes(user_id)
        
        return [{"from_user_id": a.from_user_id, "created_at": a.created_at} for a in actions]

    async def decide_on_incoming(
        self, 
        viewer_user_id: int, 
        target_user_id: int, 
        action_type: ActionTypeEnum
    ) -> dict:
        existing = await self.action_repo.get_action(viewer_user_id, target_user_id)
        if existing:
            raise ActionAlreadyExistsException(viewer_user_id, target_user_id)
        
        await self.action_repo.create(
            from_user_id=viewer_user_id,
            to_user_id=target_user_id,
            action_type=action_type
        )
        
        is_match = False
        
        if action_type == ActionTypeEnum.like:
            is_match = True
            await self.match_repo.create_match(viewer_user_id, target_user_id)

            await self._send_match_notification(viewer_user_id, target_user_id)
        
        return {"is_match": is_match}
    
    async def get_next_incoming_like(self, user_id: int, seen_ids: list[int]) -> dict:
        incoming_actions = await self.action_repo.get_incoming_likes(user_id)
        
        if not incoming_actions:
            raise NoMoreProfilesException()
        
        for action in incoming_actions:
            if action.from_user_id not in seen_ids:
                profile = await self.profile_repo.get_by_user_id(action.from_user_id)
                if profile and profile.is_active:
                    return profile
        
        raise NoMoreProfilesException()