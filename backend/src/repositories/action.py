from src.repositories.base import BaseRepository
from src.models.action import UserAction, ActionTypeEnum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, update, and_
from src.core.logger import get_repo_logger

class ActionRepository(BaseRepository[UserAction]):
    def __init__(self, session: AsyncSession):
        super().__init__(UserAction, session)
        self.logger = get_repo_logger()
        self.logger.debug(
            f"ActionRepository initialized",
            extra={"operation": "init"}
        )

    async def get_action(self, from_user_id: int, to_user_id: int) -> UserAction | None:
        self.logger.debug(
            f"Getting action",
            extra={
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "operation": "get_action"
            }
        )
        
        try:
            result = await self.session.execute(
                select(UserAction).where(
                    UserAction.from_user_id == from_user_id,
                    UserAction.to_user_id == to_user_id
                )
            )
            action = result.scalar_one_or_none()
            
            if action:
                self.logger.debug(
                    f"Action found",
                    extra={
                        "action_id": action.id,
                        "action_type": action.action_type.value if action.action_type else None,
                        "is_responded": action.is_responded,
                        "found": True,
                        "operation": "get_action"
                    }
                )
            else:
                self.logger.debug(
                    f"No action found",
                    extra={
                        "found": False,
                        "operation": "get_action"
                    }
                )
            
            return action
            
        except Exception as e:
            self.logger.error(
                f"Error getting action",
                extra={
                    "from_user_id": from_user_id,
                    "to_user_id": to_user_id,
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "operation": "get_action"
                },
                exc_info=True
            )
            raise

    async def get_next_incoming_like(self, user_id: int) -> UserAction | None:
        self.logger.debug(
            f"Getting next incoming like",
            extra={
                "user_id": user_id,
                "operation": "get_next_incoming_like"
            }
        )
        
        try:
            subquery = (
                select(
                    UserAction.from_user_id,
                    func.max(UserAction.created_at).label('last_like_time')
                )
                .where(
                    and_(
                        UserAction.to_user_id == user_id,
                        UserAction.action_type == ActionTypeEnum.like,
                        UserAction.is_responded == False
                    )
                )
                .group_by(UserAction.from_user_id)
                .subquery()
            )
            
            query = (
                select(UserAction)
                .join(
                    subquery,
                    and_(
                        UserAction.from_user_id == subquery.c.from_user_id,
                        UserAction.created_at == subquery.c.last_like_time
                    )
                )
                .where(
                    and_(
                        UserAction.to_user_id == user_id,
                        UserAction.action_type == ActionTypeEnum.like,
                        UserAction.is_responded == False
                    )
                )
                .order_by(UserAction.created_at.desc())
                .limit(1)
            )
            
            result = await self.session.execute(query)
            action = result.scalar_one_or_none()
            
            if action:
                self.logger.debug(
                    f"Found incoming like",
                    extra={
                        "user_id": user_id,
                        "from_user_id": action.from_user_id,
                        "action_id": action.id,
                        "operation": "get_next_incoming_like"
                    }
                )
            else:
                self.logger.debug(
                    f"No incoming likes found",
                    extra={
                        "user_id": user_id,
                        "operation": "get_next_incoming_like"
                    }
                )
            
            return action
            
        except Exception as e:
            self.logger.error(
                f"Error getting next incoming like",
                extra={
                    "user_id": user_id,
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "operation": "get_next_incoming_like"
                },
                exc_info=True
            )
            raise

    async def mark_as_responded(self, action_id: int) -> None:
        self.logger.debug(
            f"Marking action as responded",
            extra={
                "action_id": action_id,
                "operation": "mark_as_responded"
            }
        )
        
        try:
            await self.session.execute(
                update(UserAction)
                .where(UserAction.id == action_id)
                .values(is_responded=True)
            )
            await self.session.flush()
            
            self.logger.debug(
                f"Action marked as responded",
                extra={
                    "action_id": action_id,
                    "operation": "mark_as_responded"
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Error marking action as responded",
                extra={
                    "action_id": action_id,
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "operation": "mark_as_responded"
                },
                exc_info=True
            )
            raise
