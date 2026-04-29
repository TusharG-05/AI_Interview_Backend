import logging
import asyncio
import os
import json
from typing import Optional, Any
import redis.asyncio as redis
from .config import REDIS_URL

logger = logging.getLogger(__name__)

class InMemoryCache:
    def __init__(self, persistence_file="app/assets/cache_failover.json"):
        self._data = {}
        self._persistence_file = persistence_file
        self._load_from_disk()

    def _load_from_disk(self):
        if os.path.exists(self._persistence_file):
            try:
                with open(self._persistence_file, "r") as f:
                    self._data = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache failover file: {e}")

    def _save_to_disk(self):
        try:
            os.makedirs(os.path.dirname(self._persistence_file), exist_ok=True)
            with open(self._persistence_file, "w") as f:
                json.dump(self._data, f)
        except Exception as e:
            logger.error(f"Failed to save cache failover file: {e}")

    async def get(self, key: str) -> Optional[str]:
        return self._data.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self._data[key] = value
        self._save_to_disk()
        return True

    async def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            self._save_to_disk()
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
            # Robust connection options
            conn_kwargs = {
                "decode_responses": True,
            }
            
            # Only add SSL parameters if the URL uses SSL (rediss://)
            if self.url.startswith("rediss://"):
                # Default to skipping cert verification for cloud Redis (Upstash/Render)
                # This prevents common SSL handshake errors.
                conn_kwargs["ssl_cert_reqs"] = "none"
                logger.debug("Connecting to Redis with SSL (cert_reqs=none)")
            
            self.redis = redis.from_url(self.url, **conn_kwargs)
            
            # Test connection
            await asyncio.wait_for(self.redis.ping(), timeout=5.0)
            logger.info("Successfully connected to Redis.")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis ({type(e).__name__}: {e}). Using in-memory fallback.")
            import traceback
            logger.debug(traceback.format_exc())
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

    async def aclose(self) -> None:
        """Gracefully close the underlying Redis client (if any)."""
        if self.redis:
            try:
                await self.redis.close()
            except Exception as e:
                logger.debug(f"cache_client.aclose() error (close): {e}")
            try:
                await self.redis.connection_pool.disconnect()
            except Exception:
                pass
            self.redis = None

# Global instance
cache_client = CacheClient(REDIS_URL)
