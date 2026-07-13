"""Caching layer for ETL operations."""

import asyncio
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

import structlog

logger = structlog.get_logger()


class CacheConfig:
    """Configuration for caching behavior.

    Args:
        ttl: Time to live in seconds (None for no expiration)
        max_size: Maximum cache size in MB
        backend: Cache backend ('memory' or 'disk')
        cache_dir: Directory for disk cache
    """

    def __init__(
        self,
        ttl: Optional[float] = 3600.0,
        max_size: Optional[int] = 100,
        backend: str = "memory",
        cache_dir: str = ".cache/forgeflow",
    ):
        self.ttl = ttl
        self.max_size = max_size
        self.backend = backend
        self.cache_dir = Path(cache_dir)


class MemoryCache:
    """In-memory LRU cache with TTL support.

    Args:
        ttl: Time to live in seconds (None for no expiration)
        max_entries: Maximum number of cache entries
    """

    def __init__(self, ttl: Optional[float] = 3600.0, max_entries: int = 1000):
        self.ttl = ttl
        self.max_entries = max_entries
        self._cache: dict[str, tuple[Any, float]] = {}
        self._access_order: list[str] = []
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            if key not in self._cache:
                logger.debug("cache_miss", key=key)
                return None

            value, timestamp = self._cache[key]

            # Check if expired
            if self.ttl is not None and (time.time() - timestamp) > self.ttl:
                logger.debug("cache_expired", key=key)
                del self._cache[key]
                self._access_order.remove(key)
                return None

            # Update access order for LRU
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            logger.debug("cache_hit", key=key)
            return value

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_entries and key not in self._cache:
                oldest_key = self._access_order.pop(0)
                del self._cache[oldest_key]
                logger.debug("cache_evicted", key=oldest_key)

            self._cache[key] = (value, time.time())

            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            logger.debug("cache_set", key=key)

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            logger.info("cache_cleared")

    async def delete(self, key: str) -> bool:
        """Delete a specific cache entry.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._access_order.remove(key)
                logger.debug("cache_deleted", key=key)
                return True
            return False


class DiskCache:
    """Disk-based cache for persistent storage.

    Args:
        cache_dir: Directory to store cache files
        ttl: Time to live in seconds (None for no expiration)
    """

    def __init__(self, cache_dir: str = ".cache/forgeflow", ttl: Optional[float] = 3600.0):
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            cache_file = self._get_cache_path(key)

            if not cache_file.exists():
                logger.debug("disk_cache_miss", key=key)
                return None

            try:
                with cache_file.open("r") as f:
                    data = json.load(f)

                timestamp = data.get("timestamp", 0)

                # Check if expired
                if self.ttl is not None and (time.time() - timestamp) > self.ttl:
                    logger.debug("disk_cache_expired", key=key)
                    cache_file.unlink()
                    return None

                logger.debug("disk_cache_hit", key=key)
                return data.get("value")

            except (json.JSONDecodeError, OSError) as e:
                logger.error("disk_cache_error", key=key, error=str(e))
                return None

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        async with self._lock:
            cache_file = self._get_cache_path(key)

            try:
                data = {"value": value, "timestamp": time.time(), "key": key}

                with cache_file.open("w") as f:
                    json.dump(data, f)

                logger.debug("disk_cache_set", key=key)

            except (OSError, TypeError) as e:
                logger.error("disk_cache_write_error", key=key, error=str(e))

    async def clear(self) -> None:
        """Clear all cache files."""
        async with self._lock:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("disk_cache_cleared")

    async def delete(self, key: str) -> bool:
        """Delete a specific cache entry.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False if not found
        """
        async with self._lock:
            cache_file = self._get_cache_path(key)
            if cache_file.exists():
                cache_file.unlink()
                logger.debug("disk_cache_deleted", key=key)
                return True
            return False


class RequestCache:
    """High-level cache for HTTP requests.

    Args:
        config: CacheConfig instance
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()

        if self.config.backend == "memory":
            self._backend = MemoryCache(ttl=self.config.ttl)
        elif self.config.backend == "disk":
            self._backend = DiskCache(
                cache_dir=str(self.config.cache_dir),
                ttl=self.config.ttl,
            )
        else:
            raise ValueError(f"Unknown cache backend: {self.config.backend}")

    def _make_key(self, url: str, params: Optional[dict] = None) -> str:
        """Generate cache key from URL and parameters."""
        key_parts = [url]
        if params:
            key_parts.append(json.dumps(params, sort_keys=True))
        return "|".join(key_parts)

    async def get(self, url: str, params: Optional[dict] = None) -> Optional[Any]:
        """Get cached response for URL.

        Args:
            url: Request URL
            params: Request parameters

        Returns:
            Cached response or None
        """
        key = self._make_key(url, params)
        return await self._backend.get(key)

    async def set(self, url: str, response: Any, params: Optional[dict] = None) -> None:
        """Cache response for URL.

        Args:
            url: Request URL
            response: Response to cache
            params: Request parameters
        """
        key = self._make_key(url, params)
        await self._backend.set(key, response)

    async def clear(self) -> None:
        """Clear all cached responses."""
        await self._backend.clear()
