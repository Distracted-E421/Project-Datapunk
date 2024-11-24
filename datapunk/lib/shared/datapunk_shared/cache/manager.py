from typing import Optional, Dict, Any, Union, TypeVar, Generic
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from ..monitoring import MetricsCollector

T = TypeVar('T')  # Cache value type

class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = "lru"        # Least Recently Used
    LFU = "lfu"        # Least Frequently Used
    FIFO = "fifo"      # First In First Out
    TTL = "ttl"        # Time To Live
    RANDOM = "random"  # Random Eviction

@dataclass
class CacheConfig:
    """Configuration for cache manager"""
    max_size: int = 1000
    ttl: int = 300  # seconds
    strategy: CacheStrategy = CacheStrategy.LRU
    enable_compression: bool = True
    compression_threshold: int = 1024  # bytes
    enable_stats: bool = True
    cleanup_interval: int = 60  # seconds
    namespace_separator: str = ":"
    default_namespace: str = "default"

class CacheEntry(Generic[T]):
    """Represents a cached item"""
    def __init__(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None,
        namespace: str = "default"
    ):
        self.key = key
        self.value = value
        self.namespace = namespace
        self.created_at = datetime.utcnow()
        self.accessed_at = self.created_at
        self.access_count = 0
        self.expires_at = (
            self.created_at + timedelta(seconds=ttl)
            if ttl else None
        )

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return (
            self.expires_at is not None and
            datetime.utcnow() > self.expires_at
        )

    def access(self):
        """Record cache access"""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1

class CacheManager(Generic[T]):
    """Manages cache operations with multiple strategies"""
    def __init__(
        self,
        config: CacheConfig,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.metrics = metrics_collector
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def start(self):
        """Start cache manager"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop cache manager"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def get(
        self,
        key: str,
        namespace: Optional[str] = None
    ) -> Optional[T]:
        """Get value from cache"""
        cache_key = self._make_key(key, namespace)
        
        async with self._lock:
            entry = self._cache.get(cache_key)
            
            if not entry:
                if self.metrics:
                    await self.metrics.increment(
                        "cache.miss",
                        tags={"namespace": namespace or self.config.default_namespace}
                    )
                return None

            if entry.is_expired():
                del self._cache[cache_key]
                if self.metrics:
                    await self.metrics.increment(
                        "cache.expired",
                        tags={"namespace": namespace or self.config.default_namespace}
                    )
                return None

            entry.access()
            
            if self.metrics:
                await self.metrics.increment(
                    "cache.hit",
                    tags={"namespace": namespace or self.config.default_namespace}
                )
            
            return entry.value

    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> bool:
        """Set value in cache"""
        cache_key = self._make_key(key, namespace)
        
        async with self._lock:
            # Check cache size limit
            if len(self._cache) >= self.config.max_size:
                await self._evict_entries()

            # Store value
            self._cache[cache_key] = CacheEntry(
                key=cache_key,
                value=value,
                ttl=ttl or self.config.ttl,
                namespace=namespace or self.config.default_namespace
            )
            
            if self.metrics:
                await self.metrics.increment(
                    "cache.set",
                    tags={"namespace": namespace or self.config.default_namespace}
                )
            
            return True

    async def delete(
        self,
        key: str,
        namespace: Optional[str] = None
    ) -> bool:
        """Delete value from cache"""
        cache_key = self._make_key(key, namespace)
        
        async with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                if self.metrics:
                    await self.metrics.increment(
                        "cache.delete",
                        tags={"namespace": namespace or self.config.default_namespace}
                    )
                return True
            return False

    async def clear(
        self,
        namespace: Optional[str] = None
    ):
        """Clear cache entries"""
        async with self._lock:
            if namespace:
                # Clear specific namespace
                keys_to_delete = [
                    k for k, v in self._cache.items()
                    if v.namespace == namespace
                ]
                for key in keys_to_delete:
                    del self._cache[key]
            else:
                # Clear all entries
                self._cache.clear()
            
            if self.metrics:
                await self.metrics.increment(
                    "cache.clear",
                    tags={"namespace": namespace or "all"}
                )

    def _make_key(self, key: str, namespace: Optional[str] = None) -> str:
        """Create cache key with namespace"""
        ns = namespace or self.config.default_namespace
        return f"{ns}{self.config.namespace_separator}{key}"

    async def _cleanup_loop(self):
        """Periodic cleanup of expired entries"""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "cache.cleanup.error",
                        tags={"error": str(e)}
                    )

    async def _cleanup_expired(self):
        """Remove expired cache entries"""
        async with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if v.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                
            if self.metrics and expired_keys:
                await self.metrics.increment(
                    "cache.cleanup",
                    value=len(expired_keys)
                )

    async def _evict_entries(self):
        """Evict entries based on strategy"""
        if not self._cache:
            return

        if self.config.strategy == CacheStrategy.LRU:
            # Remove least recently used
            key_to_remove = min(
                self._cache.items(),
                key=lambda x: x[1].accessed_at
            )[0]
            
        elif self.config.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            key_to_remove = min(
                self._cache.items(),
                key=lambda x: x[1].access_count
            )[0]
            
        elif self.config.strategy == CacheStrategy.FIFO:
            # Remove oldest entry
            key_to_remove = min(
                self._cache.items(),
                key=lambda x: x[1].created_at
            )[0]
            
        elif self.config.strategy == CacheStrategy.RANDOM:
            # Remove random entry
            import random
            key_to_remove = random.choice(list(self._cache.keys()))
            
        else:  # CacheStrategy.TTL
            # Remove entry closest to expiration
            key_to_remove = min(
                self._cache.items(),
                key=lambda x: x[1].expires_at or datetime.max
            )[0]

        del self._cache[key_to_remove]
        
        if self.metrics:
            await self.metrics.increment(
                "cache.eviction",
                tags={"strategy": self.config.strategy.value}
            )

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "size": len(self._cache),
            "max_size": self.config.max_size,
            "strategy": self.config.strategy.value,
            "namespaces": {},
            "expired_entries": 0,
            "total_access_count": 0
        }
        
        for entry in self._cache.values():
            # Count by namespace
            ns_stats = stats["namespaces"].setdefault(entry.namespace, {
                "count": 0,
                "access_count": 0,
                "expired": 0
            })
            
            ns_stats["count"] += 1
            ns_stats["access_count"] += entry.access_count
            
            if entry.is_expired():
                ns_stats["expired"] += 1
                stats["expired_entries"] += 1
                
            stats["total_access_count"] += entry.access_count
            
        return stats