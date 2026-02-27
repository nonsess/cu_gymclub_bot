import json
import redis.asyncio as redis
from typing import List, Optional
from src.core.config import settings

class Cache:
    def __init__(
        self,
        redis_url: str, 
        queue_ttl: int = 3600,
        profile_ttl: int = 900,
        seen_ttl: int = 86400,
    ):
        self.__redis = redis.from_url(redis_url, decode_responses=True)
        self.__queue_ttl = queue_ttl
        self.__profile_ttl = profile_ttl
        self.__seen_ttl = seen_ttl
    
    def _queue_key(self, user_id: int) -> str:
        return f"swipe:queue:{user_id}"
    
    async def fill_queue(self, user_id: int, profile_ids: List[int]):
        queue_key = self._queue_key(user_id)
        await self.__redis.delete(queue_key)
        
        if profile_ids:
            await self.__redis.rpush(queue_key, *[str(id) for id in profile_ids])
            await self.__redis.expire(queue_key, self.__queue_ttl)
    
    async def pop_from_queue(self, user_id: int) -> Optional[int]:
        queue_key = self._queue_key(user_id)
        profile_id = await self.__redis.lpop(queue_key)
        return int(profile_id) if profile_id else None


    def _seen_key(self, user_id: int) -> str:
        return f"swipe:seen:{user_id}"
    
    async def add_seen_user_id(self, from_user_id: int, to_user_id: int):
        key = self._seen_key(from_user_id)
        await self.__redis.sadd(key, str(to_user_id))
        await self.__redis.expire(key, self.__seen_ttl)
    
    async def get_seen_user_ids(self, user_id: int) -> List[int]:
        key = self._seen_key(user_id)
        seen = await self.__redis.smembers(key)
        return [int(x) for x in seen] if seen else []


    def _profile_key(self, profile_id: int) -> str:
        return f"swipe:profile:{profile_id}"

    async def cache_profile(self, profile: dict):
        key = self._profile_key(profile['id'])
        
        await self.__redis.hset(key, mapping={
            'id': str(profile['id']),
            'user_id': str(profile['user_id']),
            'name': profile.get('name', ''),
            'description': profile.get('description', ''),
            'gender': profile.get('gender', ''),
            'age': str(profile.get('age', '')),
            'media': json.dumps(profile.get('media', [])),
            'is_active': str(profile.get('is_active', True)),
            'updated_at': str(profile.get('updated_at', '')),
            'created_at': str(profile.get('created_at', '')),
        })
        
        await self.__redis.expire(key, self.__profile_ttl)
    
    async def get_cached_profile(self, profile_id: int) -> Optional[dict]:
        key = self._profile_key(profile_id)
        data = await self.__redis.hgetall(key)
        
        if not data:
            return None
        
        return {
            'id': int(data['id']),
            'user_id': int(data['user_id']),
            'name': data['name'],
            'description': data['description'],
            'gender': data['gender'],
            'age': int(data['age']) if data['age'] else None,
            'media': json.loads(data['media']),
            'is_active': data['is_active'] == 'True',
            'updated_at': data['updated_at'],
            'created_at': data['created_at'],
        }
    
    async def invalidate_profile(self, profile_id: int):
        key = self._profile_key(profile_id)
        await self.__redis.delete(key)
    
    async def close(self):
        await self.__redis.close()

cache = Cache(settings.REDIS_URL)