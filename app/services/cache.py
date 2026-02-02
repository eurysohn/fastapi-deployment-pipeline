"""Redis cache service with connection pooling and error handling.

Provides a robust caching layer with:
- Connection pooling for performance
- Automatic reconnection on failure
- JSON serialization for complex objects
- Health check support
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service with connection management."""

    def __init__(self) -> None:
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Initialize Redis connection pool."""
        try:
            self._pool = ConnectionPool.from_url(
                str(settings.redis_url),
                max_connections=settings.redis_pool_size,
                decode_responses=True,
                socket_timeout=settings.redis_timeout,
                socket_connect_timeout=settings.redis_timeout,
            )
            self._client = redis.Redis(connection_pool=self._pool)
            # Verify connection
            await self._client.ping()
            logger.info("Redis connection established")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close Redis connection pool."""
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        logger.info("Redis connection closed")

    async def health_check(self) -> bool:
        """Check Redis connection health."""
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except RedisError:
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._client:
            return None
        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache with optional TTL."""
        if not self._client:
            return False
        try:
            serialized = json.dumps(value)
            if ttl:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)
            return True
        except (RedisError, TypeError) as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self._client:
            return False
        try:
            await self._client.delete(key)
            return True
        except RedisError as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._client:
            return False
        try:
            return bool(await self._client.exists(key))
        except RedisError:
            return False


# Singleton instance
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """Get the cache service singleton."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


async def init_cache() -> CacheService:
    """Initialize and return the cache service."""
    service = await get_cache_service()
    await service.connect()
    return service


async def close_cache() -> None:
    """Close the cache service connection."""
    global _cache_service
    if _cache_service:
        await _cache_service.disconnect()
        _cache_service = None
