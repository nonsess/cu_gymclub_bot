from src.repositories.base import BaseRepository
from src.models.match import Match
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from src.core.logger import get_repo_logger

class MatchRepository(BaseRepository[Match]):
    def __init__(self, session: AsyncSession):
        super().__init__(Match, session)
        self.logger = get_repo_logger()
        self.logger.debug(
            "MatchRepository initialized",
            extra={"operation": "init"}
        )

    async def create_match(self, user1_id: int, user2_id: int) -> Match:
        original_user1, original_user2 = user1_id, user2_id
        
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
            
        self.logger.info(
            "Creating new match between users",
            extra={
                "operation": "create_match",
                "user1_id": user1_id,
                "user2_id": user2_id,
                "original_user1_id": original_user1,
                "original_user2_id": original_user2,
                "normalized": original_user1 != user1_id or original_user2 != user2_id
            }
        )
        
        try:
            match = await self.create(
                user1_id=user1_id, 
                user2_id=user2_id, 
                is_notified=False
            )
            
            self.logger.info(
                "Successfully created match",
                extra={
                    "operation": "create_match",
                    "match_id": match.id,
                    "user1_id": match.user1_id,
                    "user2_id": match.user2_id,
                    "is_notified": match.is_notified
                }
            )
            
            return match
            
        except Exception as e:
            self.logger.error(
                "Failed to create match",
                extra={
                    "operation": "create_match",
                    "user1_id": user1_id,
                    "user2_id": user2_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
