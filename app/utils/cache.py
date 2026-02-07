"""
Caching utilities for optimization results.
Implements LRU cache with TTL for efficient frontier and other expensive operations.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar
from collections import OrderedDict
import threading

T = TypeVar('T')


@dataclass
class CacheEntry:
    """Cache entry with value and metadata."""
    value: Any
    created_at: datetime
    ttl_seconds: int
    hits: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl_seconds)


class LRUCache:
    """Thread-safe LRU cache with TTL support."""
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds (5 minutes)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }
    
    def _make_key(self, *args, **kwargs) -> str:
        """Create a hash key from arguments."""
        key_data = json.dumps({
            "args": [str(a) for a in args],
            "kwargs": {k: str(v) for k, v in sorted(kwargs.items())}
        }, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired."""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None
            
            entry = self._cache[key]
            if entry.is_expired:
                del self._cache[key]
                self._stats["misses"] += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hits += 1
            self._stats["hits"] += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        with self._lock:
            # Evict oldest if at capacity
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats["evictions"] += 1
            
            self._cache[key] = CacheEntry(
                value=value,
                created_at=datetime.now(),
                ttl_seconds=ttl or self.default_ttl,
            )
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys containing pattern."""
        with self._lock:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]
            return len(keys_to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total if total > 0 else 0
            return {
                **self._stats,
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": hit_rate,
            }


# Global cache instances
optimization_cache = LRUCache(max_size=50, default_ttl=60)  # 1 minute TTL
frontier_cache = LRUCache(max_size=20, default_ttl=300)  # 5 minutes TTL


def cached(cache: LRUCache, ttl: Optional[int] = None):
    """
    Decorator for caching function results.
    
    Usage:
        @cached(optimization_cache, ttl=120)
        def expensive_function(arg1, arg2):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Skip 'self' for method calls
            cache_args = args[1:] if args and hasattr(args[0], '__class__') else args
            key = f"{func.__name__}:{cache._make_key(*cache_args, **kwargs)}"
            
            # Check cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        wrapper.cache = cache  # Allow access to cache for invalidation
        return wrapper
    return decorator
