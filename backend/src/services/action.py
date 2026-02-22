from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.action import ActionRepository
from src.repositories.match import MatchRepository
from src.models.action import ActionTypeEnum
from src.core.exceptions.action import ActionAlreadyExistsException, SelfActionException

class ActionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.action_repo = ActionRepository(session)
        self.match_repo = MatchRepository(session)

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
            action_type=action_type,
            report_reason=report_reason if action_type == ActionTypeEnum.REPORT else None
        )
        
        is_match = False
        if action_type == ActionTypeEnum.LIKE:
            is_match = await self.action_repo.check_mutual_like(from_user_id, to_user_id)
            
            if is_match:
                await self.match_repo.create_match(from_user_id, to_user_id)
        
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
        
        if action_type == ActionTypeEnum.LIKE:
            is_match = True
            await self.match_repo.create_match(viewer_user_id, target_user_id)
        
        return {"is_match": is_match}