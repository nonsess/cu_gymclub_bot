import redis.asyncio as redis
from typing import List
from src.core.config import settings

class ActionCache:
    def __init__(self, redis_url: str, ttl: int = 3600):
        self.__redis = redis.from_url(redis_url, decode_responses=True)
        self.__ttl = ttl
    
    def _key(self, user_id: int) -> str:
        return f"swipe:seen:{user_id}"
    
    async def add_seen(self, user_id: int, profile_id: int):
        key = self._key(user_id)
        await self.__redis.sadd(key, str(profile_id))
        await self.__redis.expire(key, self.__ttl)
    
    async def get_seen(self, user_id: int) -> List[int]:
        key = self._key(user_id)
        seen = await self.__redis.smembers(key)
        return [int(x) for x in seen] if seen else []
    
    async def clear_seen(self, user_id: int):
        key = self._key(user_id)
        await self.__redis.delete(key)
    
    async def close(self):
        await self.__redis.close()

action_cache = ActionCache(settings.REDIS_URL, ttl=3600)