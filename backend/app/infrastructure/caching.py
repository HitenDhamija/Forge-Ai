"""Redis-like caching abstraction layer with in-memory backend."""

from __future__ import annotations

import asyncio
import functools
import time
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class CacheConfig:
    """Configuration for a cache instance."""

    default_ttl: int = 300
    max_size: int = 10_000
    prefix: str = ""


@dataclass
class CacheEntry:
    """A single entry in the cache."""

    key: str
    value: Any
    created_at: float
    ttl: int
    hits: int = 0


class CacheService:
    """In-memory cache with a Redis-like async interface."""

    def __init__(self, config: CacheConfig) -> None:
        self._config = config
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._total_hits = 0
        self._total_misses = 0

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    async def get(self, key: str) -> Any:
        full_key = self._full_key(key)
        with self._lock:
            entry = self._store.get(full_key)
            if entry is None:
                self._total_misses += 1
                return None
            if self._is_expired(entry):
                del self._store[full_key]
                self._total_misses += 1
                return None
            entry.hits += 1
            self._store.move_to_end(full_key)
            self._total_hits += 1
            return entry.value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        effective_ttl = ttl if ttl is not None else self._config.default_ttl
        full_key = self._full_key(key)
        with self._lock:
            if full_key in self._store:
                del self._store[full_key]
            if len(self._store) >= self._config.max_size:
                self._evict()
            self._store[full_key] = CacheEntry(
                key=full_key,
                value=value,
                created_at=time.time(),
                ttl=effective_ttl,
            )

    async def delete(self, key: str) -> None:
        full_key = self._full_key(key)
        with self._lock:
            self._store.pop(full_key, None)

    async def invalidate(self, pattern: str) -> int:
        """Delete all keys matching *pattern* (simple substring match).

        Returns the number of deleted entries.
        """
        full_pattern = self._full_key(pattern)
        removed = 0
        with self._lock:
            keys_to_remove = [k for k in self._store if full_pattern in k]
            for k in keys_to_remove:
                del self._store[k]
                removed += 1
        return removed

    async def clear(self) -> None:
        with self._lock:
            self._store.clear()

    async def exists(self, key: str) -> bool:
        full_key = self._full_key(key)
        with self._lock:
            entry = self._store.get(full_key)
            if entry is None:
                return False
            if self._is_expired(entry):
                del self._store[full_key]
                return False
            return True

    async def ttl(self, key: str) -> int:
        """Return remaining TTL in seconds, or -1 if the key does not exist."""
        full_key = self._full_key(key)
        with self._lock:
            entry = self._store.get(full_key)
            if entry is None:
                return -1
            if self._is_expired(entry):
                del self._store[full_key]
                return -1
            elapsed = time.time() - entry.created_at
            remaining = int(entry.ttl - elapsed)
            return max(remaining, 0)

    async def increment(self, key: str, amount: int = 1) -> int:
        full_key = self._full_key(key)
        with self._lock:
            entry = self._store.get(full_key)
            if entry is None or self._is_expired(entry):
                self._store[full_key] = CacheEntry(
                    key=full_key,
                    value=amount,
                    created_at=time.time(),
                    ttl=self._config.default_ttl,
                )
                return amount
            entry.value = int(entry.value) + amount
            entry.hits += 1
            self._store.move_to_end(full_key)
            return int(entry.value)

    # ------------------------------------------------------------------
    # Batch operations
    # ------------------------------------------------------------------

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(self, items: dict[str, Any], ttl: int | None = None) -> None:
        for key, value in items.items():
            await self.set(key, value, ttl)

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        with self._lock:
            total_requests = self._total_hits + self._total_misses
            hit_rate = (
                (self._total_hits / total_requests * 100) if total_requests else 0.0
            )
            return {
                "size": len(self._store),
                "max_size": self._config.max_size,
                "hits": self._total_hits,
                "misses": self._total_misses,
                "hit_rate": round(hit_rate, 2),
                "prefix": self._config.prefix,
                "default_ttl": self._config.default_ttl,
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _full_key(self, key: str) -> str:
        return f"{self._config.prefix}:{key}" if self._config.prefix else key

    def _is_expired(self, entry: CacheEntry) -> bool:
        return (time.time() - entry.created_at) > entry.ttl

    def _evict(self) -> None:
        """Remove the least-recently-used entry."""
        if self._store:
            self._store.popitem(last=False)


# ======================================================================
# Decorators
# ======================================================================


def cached(ttl: int = 300, prefix: str = "") -> Callable:
    """Decorator that caches the return value of an async function."""

    def decorator(func: Callable) -> Callable:
        cfg = CacheConfig(default_ttl=ttl, prefix=prefix or func.__name__)
        service = CacheService(cfg)

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = f"{args}:{kwargs}"
            result = await service.get(cache_key)
            if result is not None:
                return result
            result = await func(*args, **kwargs)
            await service.set(cache_key, result)
            return result

        wrapper.cache_service = service  # type: ignore[attr-defined]
        return wrapper

    return decorator


def cache_invalidate(pattern: str) -> Callable:
    """Decorator that invalidates cache entries matching *pattern* after the function runs."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            for svc in _ALL_SERVICES:
                await svc.invalidate(pattern)
            return result

        return wrapper

    return decorator


# ======================================================================
# Pre-configured cache instances
# ======================================================================

repository_cache = CacheService(CacheConfig(default_ttl=600, prefix="repo"))
knowledge_cache = CacheService(CacheConfig(default_ttl=900, prefix="knowledge"))
workflow_cache = CacheService(CacheConfig(default_ttl=300, prefix="workflow"))
prompt_cache = CacheService(CacheConfig(default_ttl=1800, prefix="prompt"))
learning_cache = CacheService(CacheConfig(default_ttl=600, prefix="learning"))
search_cache = CacheService(CacheConfig(default_ttl=120, prefix="search"))

_ALL_SERVICES = [
    repository_cache,
    knowledge_cache,
    workflow_cache,
    prompt_cache,
    learning_cache,
    search_cache,
]
