"""
Cache Service for User Service
===============================

Redis cache integration with FastAPI.
"""

from functools import lru_cache
from typing import Optional
import sys
from pathlib import Path

# Add shared module to path
shared_path = Path(__file__).parent.parent.parent.parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from shared.cache import RedisCacheService, CacheKeys
from app.core.config import settings


# Global cache instance
_cache_service: Optional[RedisCacheService] = None


def get_cache_service() -> RedisCacheService:
    """
    Get global cache service instance.

    This is initialized in the FastAPI lifespan.
    """
    if _cache_service is None:
        raise RuntimeError("Cache service not initialized")
    return _cache_service


async def init_cache():
    """
    Initialize cache service.

    Called during application startup.
    """
    global _cache_service

    print("🔌 Connecting to Redis...")

    _cache_service = RedisCacheService(
        redis_url=settings.redis_url,
        max_connections=10
    )

    await _cache_service.connect()

    print(f"✅ Redis connected: {settings.redis_url}")


async def close_cache():
    """
    Close cache service.

    Called during application shutdown.
    """
    if _cache_service:
        await _cache_service.disconnect()
        print("Redis connection closed")


# Export cache keys for convenience
__all__ = ["get_cache_service", "init_cache", "close_cache", "CacheKeys"]
