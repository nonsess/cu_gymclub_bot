from src.repositories.base import BaseRepository
from src.models.action import UserAction, ActionTypeEnum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class ActionRepository(BaseRepository[UserAction]):
    def __init__(self, session: AsyncSession):
        super().__init__(UserAction, session)

    async def get_action(self, from_user_id: int, to_user_id: int) -> UserAction | None:
        result = await self.session.execute(
            select(UserAction).where(
                UserAction.from_user_id == from_user_id,
                UserAction.to_user_id == to_user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_incoming_likes(self, user_id: int) -> list[UserAction]:
        subquery = (
            select(UserAction.to_user_id)
            .where(UserAction.from_user_id == user_id)
        )
        
        query = (
            select(UserAction)
            .where(UserAction.to_user_id == user_id)
            .where(UserAction.action_type == ActionTypeEnum.LIKE)
            .where(UserAction.from_user_id.notin_(subquery))
            .order_by(UserAction.created_at.desc())
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def check_mutual_like(self, user1_id: int, user2_id: int) -> bool:
        result = await self.session.execute(
            select(UserAction).where(
                UserAction.from_user_id == user2_id,
                UserAction.to_user_id == user1_id,
                UserAction.action_type == ActionTypeEnum.LIKE
            )
        )
        return result.scalar_one_or_none() is not None