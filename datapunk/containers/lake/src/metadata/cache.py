from typing import Dict, Any, Optional, TypeVar, Generic
from datetime import datetime, timedelta
import asyncio
import logging
from collections import OrderedDict
from .core import (
    SchemaMetadata, StatisticsMetadata, LineageMetadata,
    QualityMetadata, AccessPatternMetadata, DependencyMetadata,
    PerformanceMetadata, CacheMetadata, ResourceMetadata
)

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CacheEntry(Generic[T]):
    """Cache entry with TTL and access tracking."""
    
    def __init__(self, value: T, ttl_seconds: int):
        self.value = value
        self.expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self.last_accessed = datetime.utcnow()
        self.access_count = 1
    
    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        return datetime.utcnow() > self.expires_at
    
    def access(self) -> None:
        """Record an access to this entry."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1

class MetadataCache:
    """LRU cache for metadata with TTL."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # Separate caches for different metadata types
        self.schema_cache: OrderedDict[str, CacheEntry[SchemaMetadata]] = OrderedDict()
        self.stats_cache: OrderedDict[str, CacheEntry[StatisticsMetadata]] = OrderedDict()
        self.lineage_cache: OrderedDict[str, CacheEntry[LineageMetadata]] = OrderedDict()
        self.quality_cache: OrderedDict[str, CacheEntry[QualityMetadata]] = OrderedDict()
        self.access_pattern_cache: OrderedDict[str, CacheEntry[AccessPatternMetadata]] = OrderedDict()
        self.dependency_cache: OrderedDict[str, CacheEntry[DependencyMetadata]] = OrderedDict()
        self.performance_cache: OrderedDict[str, CacheEntry[PerformanceMetadata]] = OrderedDict()
        self.cache_metadata_cache: OrderedDict[str, CacheEntry[CacheMetadata]] = OrderedDict()
        self.resource_cache: OrderedDict[str, CacheEntry[ResourceMetadata]] = OrderedDict()
        
        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        # Background task for cleanup
        self._cleanup_task = None
    
    async def start(self) -> None:
        """Start the cache cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self) -> None:
        """Stop the cache cleanup task."""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Run cleanup every minute
                self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {str(e)}")
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries from all caches."""
        for cache in [
            self.schema_cache, self.stats_cache, self.lineage_cache,
            self.quality_cache, self.access_pattern_cache, self.dependency_cache,
            self.performance_cache, self.cache_metadata_cache, self.resource_cache
        ]:
            # Create list of expired keys to avoid modifying dict during iteration
            expired = [
                key for key, entry in cache.items()
                if entry.is_expired()
            ]
            
            for key in expired:
                del cache[key]
                self.evictions += 1
    
    def _enforce_size_limit(self, cache: OrderedDict) -> None:
        """Enforce cache size limit using LRU eviction."""
        while len(cache) >= self.max_size:
            # Find least recently accessed entry
            lru_key = min(
                cache.keys(),
                key=lambda k: (
                    cache[k].last_accessed,
                    -cache[k].access_count
                )
            )
            del cache[lru_key]
            self.evictions += 1
    
    def get_schema(self, table_name: str) -> Optional[SchemaMetadata]:
        """Get schema metadata from cache."""
        return self._get_from_cache(self.schema_cache, table_name)
    
    def set_schema(self, table_name: str, metadata: SchemaMetadata,
                  ttl: Optional[int] = None) -> None:
        """Set schema metadata in cache."""
        self._set_in_cache(self.schema_cache, table_name, metadata, ttl)
    
    def get_statistics(self, table_name: str) -> Optional[StatisticsMetadata]:
        """Get statistics metadata from cache."""
        return self._get_from_cache(self.stats_cache, table_name)
    
    def set_statistics(self, table_name: str, metadata: StatisticsMetadata,
                      ttl: Optional[int] = None) -> None:
        """Set statistics metadata in cache."""
        self._set_in_cache(self.stats_cache, table_name, metadata, ttl)
    
    def get_lineage(self, node_id: str) -> Optional[LineageMetadata]:
        """Get lineage metadata from cache."""
        return self._get_from_cache(self.lineage_cache, node_id)
    
    def set_lineage(self, node_id: str, metadata: LineageMetadata,
                   ttl: Optional[int] = None) -> None:
        """Set lineage metadata in cache."""
        self._set_in_cache(self.lineage_cache, node_id, metadata, ttl)
    
    def get_quality(self, table_name: str) -> Optional[QualityMetadata]:
        """Get quality metadata from cache."""
        return self._get_from_cache(self.quality_cache, table_name)
    
    def set_quality(self, table_name: str, metadata: QualityMetadata,
                   ttl: Optional[int] = None) -> None:
        """Set quality metadata in cache."""
        self._set_in_cache(self.quality_cache, table_name, metadata, ttl)
    
    def get_access_patterns(self, table_name: str) -> Optional[AccessPatternMetadata]:
        """Get access pattern metadata from cache."""
        return self._get_from_cache(self.access_pattern_cache, table_name)
    
    def set_access_patterns(self, table_name: str, metadata: AccessPatternMetadata,
                          ttl: Optional[int] = None) -> None:
        """Set access pattern metadata in cache."""
        self._set_in_cache(self.access_pattern_cache, table_name, metadata, ttl)
    
    def get_dependencies(self, table_name: str) -> Optional[DependencyMetadata]:
        """Get dependency metadata from cache."""
        return self._get_from_cache(self.dependency_cache, table_name)
    
    def set_dependencies(self, table_name: str, metadata: DependencyMetadata,
                        ttl: Optional[int] = None) -> None:
        """Set dependency metadata in cache."""
        self._set_in_cache(self.dependency_cache, table_name, metadata, ttl)
    
    def get_performance(self, table_name: str) -> Optional[PerformanceMetadata]:
        """Get performance metadata from cache."""
        return self._get_from_cache(self.performance_cache, table_name)
    
    def set_performance(self, table_name: str, metadata: PerformanceMetadata,
                       ttl: Optional[int] = None) -> None:
        """Set performance metadata in cache."""
        self._set_in_cache(self.performance_cache, table_name, metadata, ttl)
    
    def get_cache_metadata(self, table_name: str) -> Optional[CacheMetadata]:
        """Get cache metadata from cache."""
        return self._get_from_cache(self.cache_metadata_cache, table_name)
    
    def set_cache_metadata(self, table_name: str, metadata: CacheMetadata,
                          ttl: Optional[int] = None) -> None:
        """Set cache metadata in cache."""
        self._set_in_cache(self.cache_metadata_cache, table_name, metadata, ttl)
    
    def get_resource(self, table_name: str) -> Optional[ResourceMetadata]:
        """Get resource metadata from cache."""
        return self._get_from_cache(self.resource_cache, table_name)
    
    def set_resource(self, table_name: str, metadata: ResourceMetadata,
                    ttl: Optional[int] = None) -> None:
        """Set resource metadata in cache."""
        self._set_in_cache(self.resource_cache, table_name, metadata, ttl)
    
    def _get_from_cache(self, cache: OrderedDict,
                       key: str) -> Optional[Any]:
        """Get value from cache with TTL check."""
        if key in cache:
            entry = cache[key]
            if not entry.is_expired():
                entry.access()
                self.hits += 1
                return entry.value
            else:
                del cache[key]
                self.evictions += 1
        
        self.misses += 1
        return None
    
    def _set_in_cache(self, cache: OrderedDict,
                      key: str, value: Any,
                      ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        self._enforce_size_limit(cache)
        cache[key] = CacheEntry(value, ttl or self.default_ttl)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": hit_rate,
            "size": {
                "schema": len(self.schema_cache),
                "statistics": len(self.stats_cache),
                "lineage": len(self.lineage_cache),
                "quality": len(self.quality_cache),
                "access_patterns": len(self.access_pattern_cache),
                "dependencies": len(self.dependency_cache),
                "performance": len(self.performance_cache),
                "cache_metadata": len(self.cache_metadata_cache),
                "resource": len(self.resource_cache)
            }
        } 