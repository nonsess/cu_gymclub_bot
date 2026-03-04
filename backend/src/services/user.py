from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.user import UserRegister
from src.repositories.user import UserRepository
from src.core.logger import get_service_logger

class UserService:
    def __init__(self, session: AsyncSession):
        self.__user_repo = UserRepository(session)
        self.logger = get_service_logger()
        self.logger.debug(
            "UserService initialized",
            extra={"operation": "init"}
        )
        
    async def get_or_create_user(self, user: UserRegister):
        self.logger.debug(
            "Getting or creating user",
            extra={
                "operation": "get_or_create_user",
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name
            }
        )
        
        try:
            db_user = await self.__user_repo.create_if_not_exists(
                user.telegram_id,
                user.username,
                user.first_name
            )
            
            self.logger.info(
                f"User {'created' if db_user else 'retrieved'}",
                extra={
                    "operation": "get_or_create_user",
                    "user_id": db_user.id if db_user else None,
                    "telegram_id": user.telegram_id,
                    "is_new": db_user and db_user.created_at == db_user.updated_at
                }
            )
            
            return db_user
            
        except Exception as e:
            self.logger.error(
                "Failed to get or create user",
                extra={
                    "operation": "get_or_create_user",
                    "telegram_id": user.telegram_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise