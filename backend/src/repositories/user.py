from src.repositories.base import BaseRepository
from src.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.logger import get_repo_logger

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
        self.logger = get_repo_logger()
        self.logger.debug(
            "UserRepository initialized",
            extra={"operation": "init"}
        )

    async def get_by_telegram_id(self, telegram_id: str) -> User | None:
        self.logger.debug(
            "Getting user by telegram_id",
            extra={
                "operation": "get_by_telegram_id",
                "telegram_id": telegram_id
            }
        )
        
        try:
            result = await self.session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                self.logger.debug(
                    "User found",
                    extra={
                        "operation": "get_by_telegram_id",
                        "telegram_id": telegram_id,
                        "user_id": user.id,
                        "is_banned": user.is_banned
                    }
                )
            else:
                self.logger.debug(
                    "User not found",
                    extra={
                        "operation": "get_by_telegram_id",
                        "telegram_id": telegram_id
                    }
                )
            
            return user
            
        except Exception as e:
            self.logger.error(
                "Failed to get user by telegram_id",
                extra={
                    "operation": "get_by_telegram_id",
                    "telegram_id": telegram_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    async def create_if_not_exists(self, telegram_id: str, username: str = None, first_name: str = None) -> User:
        self.logger.debug(
            "Creating user if not exists",
            extra={
                "operation": "create_if_not_exists",
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name
            }
        )
        
        try:
            user = await self.get_by_telegram_id(telegram_id)
            
            if user:
                self.logger.debug(
                    "User already exists",
                    extra={
                        "operation": "create_if_not_exists",
                        "telegram_id": telegram_id,
                        "user_id": user.id,
                        "existing_username": user.username,
                        "existing_first_name": user.first_name
                    }
                )
                return user
            
            user = await self.create(
                telegram_id=telegram_id, 
                username=username, 
                first_name=first_name
            )
            
            self.logger.info(
                "New user created",
                extra={
                    "operation": "create_if_not_exists",
                    "telegram_id": telegram_id,
                    "user_id": user.id,
                    "username": username,
                    "first_name": first_name
                }
            )
            
            return user
            
        except Exception as e:
            self.logger.error(
                "Failed to create user",
                extra={
                    "operation": "create_if_not_exists",
                    "telegram_id": telegram_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def get_active_telegram_ids(self, limit: int = 1000, offset: int = 0) -> list[str]:
        self.logger.debug(
            "Getting active telegram_ids",
            extra={
                "operation": "get_active_telegram_ids",
                "limit": limit,
                "offset": offset
            }
        )
        
        try:
            query = (
                select(User.telegram_id)
                .where(User.is_banned == False)
                .order_by(User.id)
                .limit(limit)
                .offset(offset)
            )
            
            result = await self.session.execute(query)
            telegram_ids = result.all()
            
            self.logger.debug(
                f"Retrieved {len(telegram_ids)} active telegram_ids",
                extra={
                    "operation": "get_active_telegram_ids",
                    "count": len(telegram_ids),
                    "limit": limit,
                    "offset": offset
                }
            )
            
            return telegram_ids
            
        except Exception as e:
            self.logger.error(
                "Failed to get active telegram_ids",
                extra={
                    "operation": "get_active_telegram_ids",
                    "limit": limit,
                    "offset": offset,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise