from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.user import UserRegister
from src.repositories.user import UserRepository
from src.repositories.profile import ProfileRepository

class UserService:
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)
        self.profile_repo = ProfileRepository(session)

    async def get_or_create_user(self, user: UserRegister):
        return await self.user_repo.create_if_not_exists(
            user.telegram_id,
            user.username,
            user.first_name
        )

    async def get_user_profile(self, user_id: int):
        return await self.profile_repo.get_by_user_id(user_id)
    
    async def get_user_by_telegram_id(self, telegram_id: str):
        return await self.user_repo.get_by_telegram_id(telegram_id)