from sqlalchemy.ext.asyncio import AsyncSession

from src.models.profile import Profile
from src.schemas.profile import ProfileCreate, ProfileUpdate
from src.services.embedding import embedding_service
from src.repositories.profile import ProfileRepository
from src.core.exceptions.profile import (
    ProfileNotFoundException,
    NoMoreProfilesException,
    ProfileAlreadyExistsException
)
from src.services.cache import cache
from src.core.logger import get_service_logger

class ProfileService:
    def __init__(self, session: AsyncSession):
        self.__profile_repo = ProfileRepository(session)
        self.logger = get_service_logger()
        self.logger.debug(
            "ProfileService initialized",
            extra={"operation": "init"}
        )

    async def get_profile(self, user_id: int):
        self.logger.debug(
            "Getting profile",
            extra={
                "operation": "get_profile",
                "user_id": user_id
            }
        )
        
        try:
            profile = await self.__profile_repo.get_by_user_id(user_id)
            if not profile:
                self.logger.warning(
                    "Profile not found",
                    extra={
                        "operation": "get_profile",
                        "user_id": user_id
                    }
                )
                raise ProfileNotFoundException(user_id)
            
            self.logger.debug(
                "Profile found",
                extra={
                    "operation": "get_profile",
                    "user_id": user_id,
                    "profile_id": profile.id,
                    "is_active": profile.is_active
                }
            )
            return profile
            
        except ProfileNotFoundException:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to get profile",
                extra={
                    "operation": "get_profile",
                    "user_id": user_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    async def create_profile(
        self,
        user_id: int,
        profile_data: ProfileCreate
    ):
        self.logger.info(
            "Creating profile",
            extra={
                "operation": "create_profile",
                "user_id": user_id,
                "profile_name": profile_data.name,
                "gender": profile_data.gender.value if profile_data.gender else None,
                "age": profile_data.age,
                "has_media": bool(profile_data.media),
                "description_length": len(profile_data.description) if profile_data.description else 0
            }
        )
        
        try:
            existing = await self.__profile_repo.get_by_user_id(user_id)
            if existing:
                self.logger.warning(
                    "Profile already exists",
                    extra={
                        "operation": "create_profile",
                        "user_id": user_id,
                        "existing_profile_id": existing.id
                    }
                )
                raise ProfileAlreadyExistsException(user_id)
            
            self.logger.debug(
                "Generating embedding for description",
                extra={
                    "operation": "create_profile",
                    "user_id": user_id,
                    "description_length": len(profile_data.description)
                }
            )
            
            embedding = await embedding_service.generate_embedding(
                profile_data.description
            )
            
            profile = await self.__profile_repo.create(
                user_id=user_id,
                name=profile_data.name,
                description=profile_data.description,
                gender=profile_data.gender.value.lower(),
                age=profile_data.age,
                media=[m.model_dump() for m in profile_data.media],
                embedding=embedding,
                is_active=True
            )
            
            self.logger.info(
                "Profile created successfully",
                extra={
                    "operation": "create_profile",
                    "user_id": user_id,
                    "profile_id": profile.id,
                    "embedding_generated": embedding is not None
                }
            )
            
            return profile
            
        except ProfileAlreadyExistsException:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to create profile",
                extra={
                    "operation": "create_profile",
                    "user_id": user_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    async def update_profile(
        self,
        user_id: int,
        profile_data: ProfileUpdate
    ):
        self.logger.info(
            "Updating profile",
            extra={
                "operation": "update_profile",
                "user_id": user_id,
                "update_fields": list(profile_data.model_dump(exclude_unset=True).keys())
            }
        )
        
        try:
            profile = await self.__profile_repo.get_by_user_id(user_id)
            if not profile:
                self.logger.warning(
                    "Profile not found for update",
                    extra={
                        "operation": "update_profile",
                        "user_id": user_id
                    }
                )
                raise ProfileNotFoundException(user_id)

            update_data = profile_data.model_dump(exclude_unset=True)
            
            if 'gender' in update_data and update_data['gender'] is not None:
                if hasattr(update_data['gender'], 'value'):
                    update_data['gender'] = update_data['gender'].value.lower()
                elif isinstance(update_data['gender'], str):
                    update_data['gender'] = update_data['gender'].lower()
            
            if 'media' in update_data and update_data['media'] is not None:
                update_data['media'] = [
                    m.model_dump() if hasattr(m, 'model_dump') else m 
                    for m in update_data['media']
                ]
            
            if 'description' in update_data and update_data['description']:
                self.logger.debug(
                    "Regenerating embedding for updated description",
                    extra={
                        "operation": "update_profile",
                        "user_id": user_id,
                        "old_description_length": len(profile.description) if profile.description else 0,
                        "new_description_length": len(update_data['description'])
                    }
                )
                update_data['embedding'] = await embedding_service.generate_embedding(
                    update_data['description']
                )

            await cache.invalidate_profile(profile.id)
            self.logger.debug(
                "Profile cache invalidated",
                extra={
                    "operation": "update_profile",
                    "user_id": user_id,
                    "profile_id": profile.id
                }
            )
            
            updated_profile = await self.__profile_repo.update(profile, **update_data)
            
            self.logger.info(
                "Profile updated successfully",
                extra={
                    "operation": "update_profile",
                    "user_id": user_id,
                    "profile_id": updated_profile.id,
                    "updated_fields": list(update_data.keys())
                }
            )
            
            return updated_profile
            
        except ProfileNotFoundException:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to update profile",
                extra={
                    "operation": "update_profile",
                    "user_id": user_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

    async def get_next_profile(self, user_id: int):
        self.logger.debug(
            "Getting next profile",
            extra={
                "operation": "get_next_profile",
                "user_id": user_id
            }
        )
        
        try:
            profile_id = await cache.pop_from_queue(user_id)

            if profile_id:
                self.logger.debug(
                    f"Found profile_id {profile_id} in queue",
                    extra={
                        "operation": "get_next_profile",
                        "user_id": user_id,
                        "from_queue": True,
                        "profile_id": profile_id
                    }
                )
                
                cached = await cache.get_cached_profile(profile_id)
                if cached and cached.get('is_active'):
                    await cache.add_seen_user_id(user_id, cached["user_id"])
                    self.logger.debug(
                        "Returning cached profile",
                        extra={
                            "operation": "get_next_profile",
                            "user_id": user_id,
                            "profile_id": profile_id,
                            "from_user_id": cached["user_id"],
                            "source": "cache"
                        }
                    )
                    return cached

                profile = await self.__profile_repo.get(profile_id)

                if profile and profile.is_active:
                    profile_dict = self._profile_to_dict(profile)
                    await cache.cache_profile(profile_dict)
                    
                    await cache.add_seen_user_id(user_id, profile.user_id)
                    self.logger.debug(
                        "Returning profile from DB",
                        extra={
                            "operation": "get_next_profile",
                            "user_id": user_id,
                            "profile_id": profile_id,
                            "from_user_id": profile.user_id,
                            "source": "database"
                        }
                    )
                    return profile_dict

            current_profile = await self.__profile_repo.get_by_user_id(user_id)
            seen_user_ids = await cache.get_seen_user_ids(user_id)
            
            self.logger.debug(
                f"Seen {len(seen_user_ids)} users, looking for similar profiles",
                extra={
                    "operation": "get_next_profile",
                    "user_id": user_id,
                    "seen_count": len(seen_user_ids)
                }
            )
            
            if current_profile and current_profile.embedding is not None:
                user_embedding = current_profile.embedding
                if hasattr(user_embedding, 'tolist'):
                    user_embedding = user_embedding.tolist()
                elif not isinstance(user_embedding, list):
                    user_embedding = list(user_embedding)
                            
                profiles = await self.__profile_repo.get_similar_profiles(
                    user_embedding=user_embedding,
                    seen_user_ids=seen_user_ids + [user_id],
                    limit=10
                )
                
                if profiles:
                    self.logger.debug(
                        f"Found {len(profiles)} similar profiles",
                        extra={
                            "operation": "get_next_profile",
                            "user_id": user_id,
                            "profiles_found": len(profiles),
                            "type": "similar"
                        }
                    )
                    
                    for ind, p in enumerate(profiles):
                        if ind != 0: 
                            await cache.cache_profile(self._profile_to_dict(p))

                    profile_ids = [p.id for p in profiles[1:]]
                    await cache.fill_queue(user_id, profile_ids)

                    return profiles[0]
                    
            profiles = await self.__profile_repo.get_random_profiles(
                seen_user_ids=seen_user_ids + [user_id],
                limit=10,
            )
            
            if profiles:
                self.logger.debug(
                    f"Found {len(profiles)} random profiles",
                    extra={
                        "operation": "get_next_profile",
                        "user_id": user_id,
                        "profiles_found": len(profiles),
                        "type": "random"
                    }
                )
                
                for ind, p in enumerate(profiles):
                    if ind != 0: 
                        await cache.cache_profile(self._profile_to_dict(p))

                profile_ids = [p.id for p in profiles[1:]]
                await cache.fill_queue(user_id, profile_ids)

                return profiles[0]
            
            self.logger.warning(
                "No more profiles available",
                extra={
                    "operation": "get_next_profile",
                    "user_id": user_id
                }
            )
            raise NoMoreProfilesException()
            
        except NoMoreProfilesException:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to get next profile",
                extra={
                    "operation": "get_next_profile",
                    "user_id": user_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def _profile_to_dict(self, profile: Profile) -> dict:
        profile_dict = {
            'id': profile.id,
            'user_id': profile.user_id,
            'name': profile.name,
            'description': profile.description,
            'gender': profile.gender.value if profile.gender else None,
            'age': profile.age,
            'media': profile.media or [],
            'is_active': profile.is_active,
            'updated_at': profile.updated_at,
            'created_at': profile.created_at
        }
        
        self.logger.debug(
            "Converted profile to dict",
            extra={
                "operation": "_profile_to_dict",
                "profile_id": profile.id,
                "user_id": profile.user_id,
                "has_media": bool(profile.media)
            }
        )
        
        return profile_dict