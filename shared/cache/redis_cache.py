"""
Redis Cache Service
===================

Shared cache abstraction for all microservices.

Features:
- Connection pooling
- JSON serialization
- TTL management
- Statistics tracking
- Error handling
- Graceful degradation
"""

import json
import logging
from typing import Optional, Any, Dict
from datetime import datetime
import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheStatistics:
    """Track cache performance metrics"""

    def __init__(self):
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors = 0
        self.hit_times = []
        self.miss_times = []

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100

    @property
    def avg_hit_time_ms(self) -> float:
        """Average response time for cache hits"""
        if not self.hit_times:
            return 0.0
        return sum(self.hit_times) / len(self.hit_times) * 1000

    @property
    def avg_miss_time_ms(self) -> float:
        """Average response time for cache misses"""
        if not self.miss_times:
            return 0.0
        return sum(self.miss_times) / len(self.miss_times) * 1000

    def to_dict(self) -> dict:
        """Export statistics as dictionary"""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "errors": self.errors,
            "hit_rate": round(self.hit_rate, 2),
            "avg_hit_time_ms": round(self.avg_hit_time_ms, 3),
            "avg_miss_time_ms": round(self.avg_miss_time_ms, 3)
        }


class RedisCacheService:
    """
    Redis cache service with connection pooling and statistics.

    Usage:
        cache = RedisCacheService(redis_url="redis://localhost:6379")
        await cache.connect()

        # Set value
        await cache.set("user:123", {"name": "John"}, ttl=300)

        # Get value
        user = await cache.get("user:123")

        # Delete value
        await cache.delete("user:123")

        # Get statistics
        stats = await cache.get_stats()
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        max_connections: int = 10,
        decode_responses: bool = False  # We'll handle JSON manually
    ):
        """
        Initialize cache service.

        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connections in pool
            decode_responses: Whether to decode responses (False for binary JSON)
        """
        self.redis_url = redis_url
        self.max_connections = max_connections
        self.decode_responses = decode_responses
        self.redis: Optional[Redis] = None
        self.stats = CacheStatistics()

    async def connect(self):
        """
        Establish connection to Redis.

        Creates a connection pool for efficient resource usage.
        """
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=self.decode_responses,
                encoding="utf-8"
            )
            # Test connection
            await self.redis.ping()
            logger.info(f"✅ Connected to Redis: {self.redis_url}")
        except RedisError as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Close Redis connection pool"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    async def get(
        self,
        key: str,
        track_stats: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get value from cache.

        Args:
            key: Cache key
            track_stats: Whether to track statistics

        Returns:
            Cached value (deserialized from JSON) or None if not found

        Example:
            user = await cache.get("user:123")
            if user:
                print(f"Cache hit: {user['name']}")
            else:
                print("Cache miss")
        """
        if not self.redis:
            logger.warning("Redis not connected")
            return None

        start_time = datetime.utcnow()

        try:
            cached_data = await self.redis.get(key)

            if track_stats:
                self.stats.total_requests += 1

            if cached_data:
                # Cache HIT
                if track_stats:
                    self.stats.cache_hits += 1
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    self.stats.hit_times.append(elapsed)

                # Deserialize JSON
                return json.loads(cached_data)
            else:
                # Cache MISS
                if track_stats:
                    self.stats.cache_misses += 1
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    self.stats.miss_times.append(elapsed)

                return None

        except RedisError as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            self.stats.errors += 1
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for key '{key}': {e}")
            self.stats.errors += 1
            return None

    async def set(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (None = no expiration)

        Returns:
            True if successful, False otherwise

        Example:
            await cache.set(
                "user:123",
                {"id": "123", "name": "John"},
                ttl=300  # 5 minutes
            )
        """
        if not self.redis:
            logger.warning("Redis not connected")
            return False

        try:
            # Serialize to JSON
            json_data = json.dumps(value)

            if ttl:
                # Set with TTL
                await self.redis.setex(key, ttl, json_data)
            else:
                # Set without TTL
                await self.redis.set(key, json_data)

            return True

        except RedisError as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            self.stats.errors += 1
            return False
        except (TypeError, json.JSONEncodeError) as e:
            logger.error(f"JSON encode error for key '{key}': {e}")
            self.stats.errors += 1
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found or error

        Example:
            await cache.delete("user:123")
        """
        if not self.redis:
            logger.warning("Redis not connected")
            return False

        try:
            result = await self.redis.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")
            self.stats.errors += 1
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted

        Example:
            # Delete all user caches
            deleted = await cache.delete_pattern("user:*")
            print(f"Deleted {deleted} keys")
        """
        if not self.redis:
            logger.warning("Redis not connected")
            return 0

        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self.redis.delete(*keys)
            return 0

        except RedisError as e:
            logger.error(f"Redis DELETE PATTERN error for '{pattern}': {e}")
            self.stats.errors += 1
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        if not self.redis:
            return False

        try:
            return await self.redis.exists(key) > 0
        except RedisError as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}")
            return False

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, or None if key doesn't exist or has no expiration

        Example:
            ttl = await cache.get_ttl("user:123")
            if ttl:
                print(f"Key expires in {ttl} seconds")
        """
        if not self.redis:
            return None

        try:
            ttl = await self.redis.ttl(key)
            if ttl > 0:
                return ttl
            return None
        except RedisError as e:
            logger.error(f"Redis TTL error for key '{key}': {e}")
            return None

    async def extend_ttl(self, key: str, ttl: int) -> bool:
        """
        Extend TTL for an existing key.

        Args:
            key: Cache key
            ttl: New TTL in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self.redis:
            return False

        try:
            return await self.redis.expire(key, ttl)
        except RedisError as e:
            logger.error(f"Redis EXPIRE error for key '{key}': {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment, or None if error

        Example:
            # Track page views
            views = await cache.increment("page:home:views")
        """
        if not self.redis:
            return None

        try:
            return await self.redis.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis INCR error for key '{key}': {e}")
            return None

    async def get_stats(self) -> dict:
        """
        Get cache performance statistics.

        Returns:
            Dictionary with cache statistics

        Example:
            stats = await cache.get_stats()
            print(f"Hit rate: {stats['hit_rate']}%")
        """
        stats_dict = self.stats.to_dict()

        # Add Redis info if available
        if self.redis:
            try:
                info = await self.redis.info("stats")
                stats_dict["redis"] = {
                    "total_connections_received": info.get("total_connections_received"),
                    "total_commands_processed": info.get("total_commands_processed"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0)
                }
            except RedisError:
                pass

        return stats_dict

    async def reset_stats(self):
        """Reset cache statistics"""
        self.stats = CacheStatistics()

    async def flush_all(self):
        """
        DANGER: Delete all keys in Redis.

        Use with caution! This deletes everything.
        """
        if not self.redis:
            return

        try:
            await self.redis.flushall()
            logger.warning("⚠️ All Redis keys have been deleted")
        except RedisError as e:
            logger.error(f"Redis FLUSHALL error: {e}")


# ============================================================================
# Cache Key Builders
# ============================================================================

class CacheKeys:
    """
    Standardized cache key builders.

    Ensures consistent naming across services.
    """

    @staticmethod
    def user(user_id: str) -> str:
        """Cache key for user by ID"""
        return f"user:{user_id}"

    @staticmethod
    def user_by_email(email: str) -> str:
        """Cache key for user by email"""
        return f"user:email:{email}"

    @staticmethod
    def product(product_id: str) -> str:
        """Cache key for product by ID"""
        return f"product:{product_id}"

    @staticmethod
    def product_list(page: int = 1, limit: int = 10) -> str:
        """Cache key for product list"""
        return f"products:list:page:{page}:limit:{limit}"

    @staticmethod
    def search_results(query: str, page: int = 1) -> str:
        """Cache key for search results"""
        return f"search:{query}:page:{page}"

    @staticmethod
    def order(order_id: str) -> str:
        """Cache key for order by ID"""
        return f"order:{order_id}"

    @staticmethod
    def user_favorites(user_id: str) -> str:
        """Cache key for user favorites"""
        return f"user:{user_id}:favorites"
