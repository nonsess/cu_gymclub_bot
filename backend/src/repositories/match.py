from src.repositories.base import BaseRepository
from src.models.match import Match
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class MatchRepository(BaseRepository[Match]):
    def __init__(self, session: AsyncSession):
        super().__init__(Match, session)

    async def create_match(self, user1_id: int, user2_id: int) -> Match:
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        
        return await self.create(user1_id=user1_id, user2_id=user2_id, is_notified=False)

    async def get_by_users(self, user1_id: int, user2_id: int) -> Match | None:
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
            
        result = await self.session.execute(
            select(Match).where(
                Match.user1_id == user1_id,
                Match.user2_id == user2_id
            )
        )
        return result.scalar_one_or_none()

    async def get_user_matches(self, user_id: int) -> list[Match]:
        from sqlalchemy import or_
        result = await self.session.execute(
            select(Match).where(
                or_(Match.user1_id == user_id, Match.user2_id == user_id)
            ).order_by(Match.created_at.desc())
        )
        return list(result.scalars().all())