from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.profile import ProfileCreate, ProfileUpdate
from src.services.embedding import embedding_service
from src.repositories.profile import ProfileRepository
from src.core.exceptions.profile import (
    ProfileNotFoundException,
    NoMoreProfilesException,
    ProfileAlreadyExistsException
)
from src.services.redis import action_cache

class ProfileService:
    def __init__(self, session: AsyncSession):
        self.__profile_repo = ProfileRepository(session)

    async def get_profile(self, user_id: int):
        profile = await self.__profile_repo.get_by_user_id(user_id)
        if not profile:
            raise ProfileNotFoundException(user_id)
        return profile

    async def create_profile(
        self,
        user_id: int,
        profile_data: ProfileCreate
    ):
        existing = await self.__profile_repo.get_by_user_id(user_id)
        if existing:
            raise ProfileAlreadyExistsException(user_id)
        
        embedding = await embedding_service.generate_embedding(
            profile_data.description
        )
        
        return await self.__profile_repo.create(
            user_id=user_id,
            name=profile_data.name,
            description=profile_data.description,
            gender=profile_data.gender.value.lower(),
            age=profile_data.age,
            media=[m.model_dump() for m in profile_data.media],
            embedding=embedding,
            is_active=True
        )


    async def update_profile(
        self,
        user_id: int,
        profile_data: ProfileUpdate
    ):
        profile = await self.__profile_repo.get_by_user_id(user_id)
        if not profile:
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
            update_data['embedding'] = await embedding_service.generate_embedding(
                update_data['description']
            )
        
        return await self.__profile_repo.update(profile, **update_data)

    async def delete_profile(self, profile_id: int):
        profile = await self.__profile_repo.get(profile_id)
        if not profile:
            raise ProfileNotFoundException(profile_id)
        
        await self.__profile_repo.delete(profile)
        return True
    
    async def get_next_profile(self, user_id: int):
        current_profile = await self.__profile_repo.get_by_user_id(user_id)
        seen_ids = await action_cache.get_seen(user_id)
        
        if current_profile and current_profile.embedding is not None:
            user_embedding = current_profile.embedding
            if hasattr(user_embedding, 'tolist'):
                user_embedding = user_embedding.tolist()
            elif not isinstance(user_embedding, list):
                user_embedding = list(user_embedding)
            
            current_profile_id = current_profile.id
            
            profiles = await self.__profile_repo.get_similar_profiles(
                user_embedding=user_embedding,
                seen_ids=seen_ids + [current_profile_id],
                limit=10,
                exclude_user_id=user_id
            )
            
            if profiles:
                await action_cache.add_seen(user_id, profiles[0].id)
                return profiles[0]
        
        current_profile = await self.__profile_repo.get_by_user_id(user_id)
        current_profile_id = current_profile.id if current_profile else None
        
        profiles = await self.__profile_repo.get_random_profiles(
            seen_ids=seen_ids + ([current_profile_id] if current_profile_id else []),
            limit=10,
            exclude_user_id=user_id
        )
        
        if profiles:
            await action_cache.add_seen(user_id, profiles[0].id)
            return profiles[0]
        
        raise NoMoreProfilesException()