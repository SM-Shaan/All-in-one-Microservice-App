"""
Cache Routes - Phase 8
======================

Cache statistics and management endpoints.
"""

from fastapi import APIRouter, Depends

from app.core.cache import get_cache_service
from shared.cache import RedisCacheService

router = APIRouter()


@router.get(
    "/stats",
    summary="Get cache statistics",
    description="View cache performance metrics (hit rate, response times, etc.)"
)
async def get_cache_stats(
    cache: RedisCacheService = Depends(get_cache_service)
):
    """
    Get cache performance statistics.

    **Metrics:**
    - total_requests: Total cache requests
    - cache_hits: Number of successful cache hits
    - cache_misses: Number of cache misses (database queries)
    - hit_rate: Percentage of cache hits (aim for 80%+)
    - avg_hit_time_ms: Average response time for cache hits
    - avg_miss_time_ms: Average response time for cache misses

    Returns:
        Dictionary with cache statistics
    """
    stats = await cache.get_stats()

    return {
        "status": "success",
        "cache_stats": stats
    }


@router.post(
    "/clear",
    summary="Clear all cache",
    description="⚠️ DANGER: Delete all cached data"
)
async def clear_cache(
    cache: RedisCacheService = Depends(get_cache_service)
):
    """
    Clear all cache data.

    **Warning:** This deletes all cached data!

    Use cases:
    - Testing cache invalidation
    - Forcing fresh data from database
    - Development/debugging

    ⚠️ In production, this should require admin permissions!

    Returns:
        Success message
    """
    await cache.flush_all()

    return {
        "status": "success",
        "message": "All cache data has been cleared"
    }


@router.post(
    "/stats/reset",
    summary="Reset cache statistics",
    description="Reset cache performance counters to zero"
)
async def reset_cache_stats(
    cache: RedisCacheService = Depends(get_cache_service)
):
    """
    Reset cache statistics counters.

    Useful for:
    - Starting fresh performance measurements
    - Testing cache behavior
    - Development/debugging

    Returns:
        Success message
    """
    await cache.reset_stats()

    return {
        "status": "success",
        "message": "Cache statistics have been reset"
    }
