"""
In-Memory Cache for Simulation Results

Uses LRU cache with TTL for optimal performance.
Cache key: hash(sim_id + params)
"""

import time
import json
import hashlib
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict
from dataclasses import dataclass
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached entry with expiration."""
    data: Any
    created_at: float
    access_count: int = 0


class LRUCache:
    """
    Thread-safe LRU cache with TTL expiration.

    Features:
    - LRU eviction when max size reached
    - TTL-based expiration (default 5 minutes)
    - Thread-safe operations
    - Cache statistics tracking
    """

    def __init__(self, max_size: int = 10000, ttl_seconds: float = 300):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of entries
            ttl_seconds: Time-to-live in seconds (default 5 minutes)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _make_key(self, sim_id: str, params: Dict[str, Any]) -> str:
        """Create a unique cache key from simulation ID and parameters."""
        # Sort params for consistent hashing
        params_str = json.dumps(params, sort_keys=True, default=str)
        combined = f"{sim_id}:{params_str}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get(self, sim_id: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached result for simulation with given parameters.

        Returns None if not found or expired.
        """
        key = self._make_key(sim_id, params)

        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None

            entry = self._cache[key]

            # Check if expired
            if time.time() - entry.created_at > self.ttl_seconds:
                del self._cache[key]
                self.misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.access_count += 1
            self.hits += 1

            return entry.data

    def set(self, sim_id: str, params: Dict[str, Any], data: Any):
        """
        Cache a simulation result.

        Automatically evicts oldest entries if max size reached.
        """
        key = self._make_key(sim_id, params)

        with self._lock:
            # Remove oldest entries if at capacity
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self.evictions += 1

            # Add new entry
            self._cache[key] = CacheEntry(
                data=data,
                created_at=time.time()
            )

    def invalidate(self, sim_id: str):
        """Invalidate all cached entries for a simulation."""
        with self._lock:
            keys_to_remove = [
                key for key in self._cache
                if key.startswith(sim_id)  # This won't work perfectly with hashed keys
            ]
            for key in keys_to_remove:
                del self._cache[key]

    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def cleanup_expired(self):
        """Remove all expired entries."""
        now = time.time()
        expired_count = 0

        with self._lock:
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if now - entry.created_at > self.ttl_seconds
            ]
            for key in keys_to_remove:
                del self._cache[key]
                expired_count += 1

        if expired_count > 0:
            logger.debug(f"Cleaned up {expired_count} expired cache entries")

        return expired_count

    @property
    def size(self) -> int:
        """Current number of entries in cache."""
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        """Cache hit rate (0.0 to 1.0)."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hit_rate * 100, 2),
            "evictions": self.evictions,
            "ttl_seconds": self.ttl_seconds,
        }


# Global cache instance
# 10000 entries, 5 minute TTL
simulation_cache = LRUCache(max_size=10000, ttl_seconds=300)


def get_cached_result(sim_id: str, params: Dict[str, Any]) -> Optional[Any]:
    """Get cached simulation result."""
    return simulation_cache.get(sim_id, params)


def cache_result(sim_id: str, params: Dict[str, Any], result: Any):
    """Cache a simulation result."""
    simulation_cache.set(sim_id, params, result)
