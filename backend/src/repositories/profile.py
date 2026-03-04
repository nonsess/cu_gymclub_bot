from src.repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.profile import Profile
from sqlalchemy import select, func
from typing import List
from src.core.logger import get_repo_logger

class ProfileRepository(BaseRepository[Profile]):
    def __init__(self, session: AsyncSession):
        super().__init__(Profile, session)
        self.logger = get_repo_logger()
        self.logger.debug(
            "ProfileRepository initialized",
            extra={"operation": "init"}
        )

    async def get_by_user_id(self, user_id: int) -> Profile | None:
        self.logger.debug(
            "Getting profile by user_id",
            extra={
                "operation": "get_by_user_id",
                "user_id": user_id
            }
        )
        
        try:
            result = await self.session.execute(
                select(Profile).where(Profile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            
            if profile:
                self.logger.debug(
                    "Profile found",
                    extra={
                        "operation": "get_by_user_id",
                        "user_id": user_id,
                        "profile_id": profile.id,
                        "is_active": profile.is_active
                    }
                )
            else:
                self.logger.debug(
                    "Profile not found",
                    extra={
                        "operation": "get_by_user_id",
                        "user_id": user_id
                    }
                )
            
            return profile
            
        except Exception as e:
            self.logger.error(
                "Failed to get profile by user_id",
                extra={
                    "operation": "get_by_user_id",
                    "user_id": user_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    async def get_similar_profiles(
        self, 
        user_embedding: List[float], 
        seen_user_ids: List[int], 
        limit: int = 10,
    ) -> List[Profile]:
        self.logger.debug(
            "Getting similar profiles",
            extra={
                "operation": "get_similar_profiles",
                "seen_users_count": len(seen_user_ids),
                "limit": limit,
                "embedding_length": len(user_embedding) if user_embedding else 0
            }
        )
        
        try:
            query = (
                select(Profile)
                .where(Profile.user_id.notin_(seen_user_ids))
                .where(Profile.is_active == True)
            )
            
            query = (
                query
                .order_by(Profile.embedding.op('<->')(user_embedding))
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            profiles = list(result.scalars().all())
            
            self.logger.debug(
                f"Found {len(profiles)} similar profiles",
                extra={
                    "operation": "get_similar_profiles",
                    "found_count": len(profiles),
                    "limit": limit,
                    "seen_users_count": len(seen_user_ids)
                }
            )
            
            return profiles
            
        except Exception as e:
            self.logger.error(
                "Failed to get similar profiles",
                extra={
                    "operation": "get_similar_profiles",
                    "seen_users_count": len(seen_user_ids),
                    "limit": limit,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    async def get_random_profiles(
        self, 
        seen_user_ids: List[int], 
        limit: int = 10,
    ) -> List[Profile]:
        self.logger.debug(
            "Getting random profiles",
            extra={
                "operation": "get_random_profiles",
                "seen_users_count": len(seen_user_ids),
                "limit": limit
            }
        )
        
        try:
            query = (
                select(Profile)
                .where(Profile.user_id.notin_(seen_user_ids))
                .where(Profile.is_active == True)
            )
                    
            query = (
                query
                .order_by(func.random())
                .limit(limit)
            )
            
            result = await self.session.execute(query)
            profiles = list(result.scalars().all())
            
            self.logger.debug(
                f"Found {len(profiles)} random profiles",
                extra={
                    "operation": "get_random_profiles",
                    "found_count": len(profiles),
                    "limit": limit,
                    "seen_users_count": len(seen_user_ids)
                }
            )
            
            return profiles
            
        except Exception as e:
            self.logger.error(
                "Failed to get random profiles",
                extra={
                    "operation": "get_random_profiles",
                    "seen_users_count": len(seen_user_ids),
                    "limit": limit,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise