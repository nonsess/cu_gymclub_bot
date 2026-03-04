from src.repositories.base import BaseRepository
from src.models.action import UserAction, ActionTypeEnum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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

    async def get_incoming_likes(self, user_id: int) -> list[UserAction]:
        self.logger.debug(
            f"Getting incoming likes",
            extra={
                "user_id": user_id,
                "operation": "get_incoming_likes"
            }
        )
        
        try:
            subquery = (
                select(UserAction.to_user_id)
                .where(UserAction.from_user_id == user_id)
            )
            
            query = (
                select(UserAction)
                .where(UserAction.to_user_id == user_id)
                .where(UserAction.action_type == ActionTypeEnum.like)
                .where(UserAction.from_user_id.notin_(subquery))
                .order_by(UserAction.created_at.desc())
            )
            
            result = await self.session.execute(query)
            actions = list(result.scalars().all())
            
            self.logger.debug(
                f"Found {len(actions)} incoming likes",
                extra={
                    "user_id": user_id,
                    "count": len(actions),
                    "operation": "get_incoming_likes"
                }
            )
            
            return actions
            
        except Exception as e:
            self.logger.error(
                f"Error getting incoming likes",
                extra={
                    "user_id": user_id,
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "operation": "get_incoming_likes"
                },
                exc_info=True
            )
            raise

    async def check_mutual_like(self, user1_id: int, user2_id: int) -> bool:
        self.logger.debug(
            f"Checking mutual like",
            extra={
                "user1_id": user1_id,
                "user2_id": user2_id,
                "operation": "check_mutual_like"
            }
        )
        
        try:
            result = await self.session.execute(
                select(UserAction).where(
                    UserAction.from_user_id == user2_id,
                    UserAction.to_user_id == user1_id,
                    UserAction.action_type == ActionTypeEnum.like
                )
            )
            
            is_mutual = result.scalar_one_or_none() is not None
            
            self.logger.debug(
                f"Mutual like check result: {is_mutual}",
                extra={
                    "user1_id": user1_id,
                    "user2_id": user2_id,
                    "is_mutual": is_mutual,
                    "operation": "check_mutual_like"
                }
            )
            
            return is_mutual
            
        except Exception as e:
            self.logger.error(
                f"Error checking mutual like",
                extra={
                    "user1_id": user1_id,
                    "user2_id": user2_id,
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "operation": "check_mutual_like"
                },
                exc_info=True
            )
            raise