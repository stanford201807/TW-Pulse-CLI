"""Data caching layer using diskcache."""

import hashlib
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

import diskcache

from pulse.core.config import settings
from pulse.utils.logger import get_logger

log = get_logger(__name__)

T = TypeVar("T")


class DataCache:
    """Disk-based cache for stock data."""

    def __init__(
        self,
        cache_dir: Path | None = None,
        ttl: int | None = None,
    ):
        """
        Initialize data cache.
        
        Args:
            cache_dir: Cache directory path
            ttl: Default TTL in seconds
        """
        self.cache_dir = cache_dir or (settings.base_dir / settings.data.cache_dir)
        self.ttl = ttl or settings.data.cache_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache = diskcache.Cache(str(self.cache_dir))

    def _make_key(self, prefix: str, *args: Any, **kwargs: Any) -> str:
        """Generate cache key from prefix and arguments."""
        key_parts = [prefix] + [str(a) for a in args]

        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend([f"{k}={v}" for k, v in sorted_kwargs])

        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            return self._cache.get(key)
        except Exception as e:
            log.warning(f"Cache get error for {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (optional)
            
        Returns:
            True if successful
        """
        try:
            expire = ttl or self.ttl
            self._cache.set(key, value, expire=expire)
            return True
        except Exception as e:
            log.warning(f"Cache set error for {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted
        """
        try:
            return self._cache.delete(key)
        except Exception as e:
            log.warning(f"Cache delete error for {key}: {e}")
            return False

    def clear(self) -> None:
        """Clear all cached data."""
        try:
            self._cache.clear()
            log.info("Cache cleared")
        except Exception as e:
            log.error(f"Cache clear error: {e}")

    def get_stock(self, ticker: str) -> Any | None:
        """Get cached stock data."""
        key = self._make_key("stock", ticker.upper())
        return self.get(key)

    def set_stock(self, ticker: str, data: Any, ttl: int | None = None) -> bool:
        """Cache stock data."""
        key = self._make_key("stock", ticker.upper())
        return self.set(key, data, ttl)

    def get_broker(self, ticker: str, date: str) -> Any | None:
        """Get cached broker summary."""
        key = self._make_key("broker", ticker.upper(), date)
        return self.get(key)

    def set_broker(self, ticker: str, date: str, data: Any, ttl: int | None = None) -> bool:
        """Cache broker summary."""
        key = self._make_key("broker", ticker.upper(), date)
        # Broker data should be cached longer (1 day)
        return self.set(key, data, ttl or 86400)

    def get_technical(self, ticker: str) -> Any | None:
        """Get cached technical indicators."""
        key = self._make_key("technical", ticker.upper())
        return self.get(key)

    def set_technical(self, ticker: str, data: Any, ttl: int | None = None) -> bool:
        """Cache technical indicators."""
        key = self._make_key("technical", ticker.upper())
        return self.set(key, data, ttl)

    def get_fundamental(self, ticker: str) -> Any | None:
        """Get cached fundamental data."""
        key = self._make_key("fundamental", ticker.upper())
        return self.get(key)

    def set_fundamental(self, ticker: str, data: Any, ttl: int | None = None) -> bool:
        """Cache fundamental data."""
        key = self._make_key("fundamental", ticker.upper())
        # Fundamental data changes less frequently
        return self.set(key, data, ttl or 86400)

    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "volume": self._cache.volume(),
            "directory": str(self.cache_dir),
        }

    def close(self) -> None:
        """Close cache connection."""
        self._cache.close()


def cached(
    prefix: str,
    ttl: int | None = None,
    key_args: list | None = None,
):
    """
    Decorator for caching function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Cache TTL in seconds
        key_args: List of argument names to use for cache key
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            cache = DataCache()

            # Build cache key
            if key_args:
                cache_kwargs = {k: kwargs.get(k) for k in key_args if k in kwargs}
            else:
                cache_kwargs = kwargs

            key = cache._make_key(prefix, *args[1:], **cache_kwargs)  # Skip self

            # Try cache first
            cached_value = cache.get(key)
            if cached_value is not None:
                log.debug(f"Cache hit for {prefix}")
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                cache.set(key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            cache = DataCache()

            if key_args:
                cache_kwargs = {k: kwargs.get(k) for k in key_args if k in kwargs}
            else:
                cache_kwargs = kwargs

            key = cache._make_key(prefix, *args[1:], **cache_kwargs)

            cached_value = cache.get(key)
            if cached_value is not None:
                log.debug(f"Cache hit for {prefix}")
                return cached_value

            result = func(*args, **kwargs)

            if result is not None:
                cache.set(key, result, ttl)

            return result

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Global cache instance
cache = DataCache()
