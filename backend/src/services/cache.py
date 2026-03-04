import json
import redis.asyncio as redis
from typing import List, Optional
from src.core.config import settings
from src.core.logger import get_cache_logger

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
        self.logger = get_cache_logger()
        self.logger.debug(
            "Cache initialized",
            extra={
                "operation": "init",
                "redis_url": redis_url,
                "queue_ttl": queue_ttl,
                "profile_ttl": profile_ttl,
                "seen_ttl": seen_ttl
            }
        )
    
    def _queue_key(self, user_id: int) -> str:
        return f"swipe:queue:{user_id}"
    
    async def fill_queue(self, user_id: int, profile_ids: List[int]):
        self.logger.debug(
            "Filling queue",
            extra={
                "operation": "fill_queue",
                "user_id": user_id,
                "profile_count": len(profile_ids)
            }
        )
        
        try:
            queue_key = self._queue_key(user_id)
            await self.__redis.delete(queue_key)
            
            if profile_ids:
                await self.__redis.rpush(queue_key, *[str(id) for id in profile_ids])
                await self.__redis.expire(queue_key, self.__queue_ttl)
                
                self.logger.debug(
                    f"Queue filled with {len(profile_ids)} profiles",
                    extra={
                        "operation": "fill_queue",
                        "user_id": user_id,
                        "profile_count": len(profile_ids),
                        "queue_key": queue_key,
                        "ttl": self.__queue_ttl
                    }
                )
            else:
                self.logger.debug(
                    "Queue cleared (no profiles)",
                    extra={
                        "operation": "fill_queue",
                        "user_id": user_id
                    }
                )
                
        except Exception as e:
            self.logger.error(
                "Failed to fill queue",
                extra={
                    "operation": "fill_queue",
                    "user_id": user_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def pop_from_queue(self, user_id: int) -> Optional[int]:
        self.logger.debug(
            "Popping from queue",
            extra={
                "operation": "pop_from_queue",
                "user_id": user_id
            }
        )
        
        try:
            queue_key = self._queue_key(user_id)
            profile_id = await self.__redis.lpop(queue_key)
            
            if profile_id:
                self.logger.debug(
                    f"Popped profile {profile_id} from queue",
                    extra={
                        "operation": "pop_from_queue",
                        "user_id": user_id,
                        "profile_id": int(profile_id)
                    }
                )
                return int(profile_id)
            else:
                self.logger.debug(
                    "Queue is empty",
                    extra={
                        "operation": "pop_from_queue",
                        "user_id": user_id
                    }
                )
                return None
                
        except Exception as e:
            self.logger.error(
                "Failed to pop from queue",
                extra={
                    "operation": "pop_from_queue",
                    "user_id": user_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise


    def _seen_key(self, user_id: int) -> str:
        return f"swipe:seen:{user_id}"
    
    async def add_seen_user_id(self, from_user_id: int, to_user_id: int):
        self.logger.debug(
            "Adding seen user",
            extra={
                "operation": "add_seen_user_id",
                "from_user_id": from_user_id,
                "to_user_id": to_user_id
            }
        )
        
        try:
            key = self._seen_key(from_user_id)
            await self.__redis.sadd(key, str(to_user_id))
            await self.__redis.expire(key, self.__seen_ttl)
            
            self.logger.debug(
                f"User {to_user_id} added to seen set",
                extra={
                    "operation": "add_seen_user_id",
                    "from_user_id": from_user_id,
                    "to_user_id": to_user_id,
                    "seen_key": key,
                    "ttl": self.__seen_ttl
                }
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to add seen user",
                extra={
                    "operation": "add_seen_user_id",
                    "from_user_id": from_user_id,
                    "to_user_id": to_user_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def get_seen_user_ids(self, user_id: int) -> List[int]:
        self.logger.debug(
            "Getting seen user ids",
            extra={
                "operation": "get_seen_user_ids",
                "user_id": user_id
            }
        )
        
        try:
            key = self._seen_key(user_id)
            seen = await self.__redis.smembers(key)
            seen_ids = [int(x) for x in seen] if seen else []
            
            self.logger.debug(
                f"Retrieved {len(seen_ids)} seen users",
                extra={
                    "operation": "get_seen_user_ids",
                    "user_id": user_id,
                    "count": len(seen_ids)
                }
            )
            
            return seen_ids
            
        except Exception as e:
            self.logger.error(
                "Failed to get seen user ids",
                extra={
                    "operation": "get_seen_user_ids",
                    "user_id": user_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise


    def _profile_key(self, profile_id: int) -> str:
        return f"swipe:profile:{profile_id}"

    async def cache_profile(self, profile: dict):
        self.logger.debug(
            "Caching profile",
            extra={
                "operation": "cache_profile",
                "profile_id": profile.get('id'),
                "user_id": profile.get('user_id')
            }
        )
        
        try:
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
            
            self.logger.debug(
                f"Profile {profile['id']} cached",
                extra={
                    "operation": "cache_profile",
                    "profile_id": profile['id'],
                    "user_id": profile['user_id'],
                    "ttl": self.__profile_ttl,
                    "has_media": bool(profile.get('media'))
                }
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to cache profile",
                extra={
                    "operation": "cache_profile",
                    "profile_id": profile.get('id'),
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def get_cached_profile(self, profile_id: int) -> Optional[dict]:
        self.logger.debug(
            "Getting cached profile",
            extra={
                "operation": "get_cached_profile",
                "profile_id": profile_id
            }
        )
        
        try:
            key = self._profile_key(profile_id)
            data = await self.__redis.hgetall(key)
            
            if not data:
                self.logger.debug(
                    f"Profile {profile_id} not found in cache",
                    extra={
                        "operation": "get_cached_profile",
                        "profile_id": profile_id,
                        "found": False
                    }
                )
                return None
            
            profile = {
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
            
            self.logger.debug(
                f"Profile {profile_id} retrieved from cache",
                extra={
                    "operation": "get_cached_profile",
                    "profile_id": profile_id,
                    "found": True,
                    "user_id": profile['user_id'],
                    "has_media": bool(profile['media'])
                }
            )
            
            return profile
            
        except Exception as e:
            self.logger.error(
                "Failed to get cached profile",
                extra={
                    "operation": "get_cached_profile",
                    "profile_id": profile_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def invalidate_profile(self, profile_id: int):
        self.logger.debug(
            "Invalidating profile cache",
            extra={
                "operation": "invalidate_profile",
                "profile_id": profile_id
            }
        )
        
        try:
            key = self._profile_key(profile_id)
            await self.__redis.delete(key)
            
            self.logger.debug(
                f"Profile {profile_id} cache invalidated",
                extra={
                    "operation": "invalidate_profile",
                    "profile_id": profile_id
                }
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to invalidate profile cache",
                extra={
                    "operation": "invalidate_profile",
                    "profile_id": profile_id,
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def close(self):
        self.logger.debug(
            "Closing cache connection",
            extra={"operation": "close"}
        )
        
        try:
            await self.__redis.close()
            self.logger.debug(
                "Cache connection closed",
                extra={"operation": "close"}
            )
        except Exception as e:
            self.logger.error(
                "Failed to close cache connection",
                extra={
                    "operation": "close",
                    "error_type": type(e).__name__,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

cache = Cache(settings.REDIS_URL)