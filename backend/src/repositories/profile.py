from src.repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.profile import Profile
from sqlalchemy import select
from typing import List

class ProfileRepository(BaseRepository[Profile]):
    def __init__(self, session: AsyncSession):
        super().__init__(Profile, session)

    async def get_by_user_id(self, user_id: int) -> Profile | None:
        result = await self.session.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_similar_profiles(
        self, 
        user_embedding: List[float], 
        seen_ids: List[int], 
        limit: int = 10,
        exclude_user_id: int | None = None
    ) -> List[Profile]:
        query = (
            select(Profile)
            .where(Profile.id.notin_(seen_ids))
            .where(Profile.is_active == True)
        )
        
        if exclude_user_id:
            query = query.where(Profile.user_id != exclude_user_id)
        
        query = (
            query
            .order_by(Profile.embedding.op('<->')(user_embedding))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_random_profiles(
        self, 
        seen_ids: List[int], 
        limit: int = 10,
        exclude_user_id: int | None = None
    ) -> List[Profile]:
        from sqlalchemy import func
        query = (
            select(Profile)
            .where(Profile.id.notin_(seen_ids))
            .where(Profile.is_active == True)
        )
        
        if exclude_user_id:
            query = query.where(Profile.user_id != exclude_user_id)
        
        query = (
            query
            .order_by(func.random())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())