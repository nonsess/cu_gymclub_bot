from src.repositories.base import BaseRepository
from src.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_telegram_id(self, telegram_id: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create_if_not_exists(self, telegram_id: str, username: str = None, first_name: str = None) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            user = await self.create(telegram_id=telegram_id, username=username, first_name=first_name)
        return user
    
    async def get_active_telegram_ids(self, limit: int = 1000, offset: int = 0) -> list[tuple[int, str]]:
        query = (
            select(User.telegram_id)
            .where(User.is_banned == False)
            .order_by(User.id)
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        return result.all()