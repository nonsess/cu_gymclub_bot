from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.user import UserRegister
from src.repositories.user import UserRepository

class UserService:
    def __init__(self, session: AsyncSession):
        self.__user_repo = UserRepository(session)
        
    async def get_or_create_user(self, user: UserRegister):
        return await self.__user_repo.create_if_not_exists(
            user.telegram_id,
            user.username,
            user.first_name
        )
