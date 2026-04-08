import logging
import asyncio
from typing import Optional, Any
import redis.asyncio as redis
from .config import REDIS_URL

logger = logging.getLogger(__name__)

class InMemoryCache:
    """A simple in-memory cache fallback for when Redis is unavailable."""
    def __init__(self):
        self._data = {}
        self._expiry = {}

    async def get(self, key: str) -> Optional[str]:
        if key in self._data:
            # Check expiry
            if key in self._expiry and asyncio.get_event_loop().time() > self._expiry[key]:
                del self._data[key]
                del self._expiry[key]
                return None
            return self._data[key]
        return None

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self._data[key] = value
        if ex:
            self._expiry[key] = asyncio.get_event_loop().time() + ex
        return True

    async def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            if key in self._expiry:
                del self._expiry[key]
            return True
        return False

class CacheClient:
    """Unified cache client that switches between Redis and InMemory."""
    def __init__(self, url: str):
        self.url = url
        self.redis = None
        self.in_memory = InMemoryCache()
        self._initialized = False

    async def _ensure_redis(self):
        if self._initialized:
            return
        
        try:
            self.redis = redis.from_url(self.url, decode_responses=True)
            # Test connection
            await asyncio.wait_for(self.redis.ping(), timeout=1.0)
            logger.info("Successfully connected to Redis.")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis ({e}). Using in-memory fallback.")
            self.redis = None
        
        self._initialized = True

    async def get(self, key: str) -> Optional[str]:
        await self._ensure_redis()
        val = None
        if self.redis:
            try:
                val = await self.redis.get(key)
                if val: logger.debug(f"Cache Hit (Redis): {key}")
            except Exception as e:
                logger.error(f"Redis get error: {e}. Falling back to in-memory.")
                self.redis = None
        
        if val is None:
            val = await self.in_memory.get(key)
            if val: logger.debug(f"Cache Hit (InMemory): {key}")
            else: logger.debug(f"Cache Miss: {key}")
        return val

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        await self._ensure_redis()
        logger.debug(f"Cache Set: {key} (ex={ex})")
        if self.redis:
            try:
                return await self.redis.set(key, value, ex=ex)
            except Exception as e:
                logger.error(f"Redis set error: {e}. Falling back to in-memory.")
                self.redis = None
        return await self.in_memory.set(key, value, ex=ex)

    async def delete(self, key: str) -> bool:
        await self._ensure_redis()
        if self.redis:
            try:
                return await self.redis.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}. Falling back to in-memory.")
                self.redis = None
        return await self.in_memory.delete(key)

# Global instance
cache_client = CacheClient(REDIS_URL)
