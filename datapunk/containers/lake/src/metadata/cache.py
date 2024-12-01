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
from abc import ABC, abstractmethod
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sentence_transformers import SentenceTransformer
import faiss
import torch
import json

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

class CacheStrategy(ABC):
    """Base class for cache strategies."""
    
    @abstractmethod
    async def should_cache(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Determine if an item should be cached."""
        pass
    
    @abstractmethod
    async def should_evict(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Determine if an item should be evicted."""
        pass
    
    @abstractmethod
    async def get_priority(self, key: str, metadata: Dict[str, Any]) -> float:
        """Get cache priority for an item."""
        pass

class PredictiveCacheStrategy(CacheStrategy):
    """Cache strategy using ML for prediction."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.access_history: Dict[str, List[Dict[str, Any]]] = {}
        self.feature_columns = [
            'hour_of_day',
            'day_of_week',
            'access_count',
            'avg_latency',
            'data_size',
            'last_access_gap'
        ]
    
    async def should_cache(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Predict if item should be cached based on patterns."""
        features = await self._extract_features(key, metadata)
        if not features:
            return False
        
        # Use DBSCAN to detect access pattern clusters
        X = self.scaler.fit_transform(np.array([features]))
        clustering = DBSCAN(eps=0.3, min_samples=2).fit(X)
        
        # Items in clusters are more likely to be accessed again
        return clustering.labels_[0] != -1
    
    async def should_evict(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Predict if item should be evicted."""
        features = await self._extract_features(key, metadata)
        if not features:
            return True
        
        # Calculate time since last access
        last_access = metadata.get('last_access_time', datetime.min)
        time_gap = (datetime.utcnow() - last_access).total_seconds()
        
        # Predict future access probability
        access_probability = await self._predict_access_probability(features)
        
        return access_probability < 0.3 and time_gap > 3600  # 1 hour
    
    async def get_priority(self, key: str, metadata: Dict[str, Any]) -> float:
        """Calculate cache priority using ML predictions."""
        features = await self._extract_features(key, metadata)
        if not features:
            return 0.0
        
        access_probability = await self._predict_access_probability(features)
        data_size = metadata.get('size_bytes', 0)
        access_count = metadata.get('access_count', 0)
        
        # Weighted scoring
        size_score = 1.0 / (1 + np.log1p(data_size))
        count_score = np.log1p(access_count) / 10.0
        
        return 0.5 * access_probability + 0.3 * size_score + 0.2 * count_score
    
    async def _extract_features(self, key: str, metadata: Dict[str, Any]) -> Optional[List[float]]:
        """Extract features for ML prediction."""
        try:
            now = datetime.utcnow()
            last_access = metadata.get('last_access_time', now)
            
            features = [
                float(now.hour),
                float(now.weekday()),
                float(metadata.get('access_count', 0)),
                float(metadata.get('avg_latency_ms', 0)),
                float(metadata.get('size_bytes', 0)),
                float((now - last_access).total_seconds())
            ]
            
            return features
        except Exception as e:
            logging.error(f"Error extracting features: {e}")
            return None
    
    async def _predict_access_probability(self, features: List[float]) -> float:
        """Predict probability of future access."""
        try:
            X = self.scaler.transform(np.array([features]))
            # Simple heuristic-based prediction
            recency_score = 1.0 / (1 + features[5] / 3600)  # Time gap
            frequency_score = np.log1p(features[2]) / 10.0  # Access count
            temporal_score = np.cos(np.pi * features[0] / 12)  # Hour of day
            
            return 0.4 * recency_score + 0.4 * frequency_score + 0.2 * temporal_score
        except Exception as e:
            logging.error(f"Error predicting access probability: {e}")
            return 0.0

class SemanticCacheStrategy(CacheStrategy):
    """Cache strategy using semantic similarity."""
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = faiss.IndexFlatL2(384)  # Dimension of embeddings
        self.cached_queries: Dict[str, np.ndarray] = {}
    
    async def should_cache(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Determine caching based on semantic similarity."""
        query = metadata.get('query', '')
        if not query:
            return False
        
        try:
            # Get query embedding
            embedding = self.model.encode([query])[0]
            
            if len(self.cached_queries) > 0:
                # Search for similar queries
                D, I = self.index.search(
                    np.array([embedding]).astype('float32'), 
                    min(5, len(self.cached_queries))
                )
                
                # Cache if no similar queries found
                return D[0][0] > 0.5 if len(D) > 0 else True
            else:
                return True
        except Exception as e:
            logging.error(f"Error in semantic cache decision: {e}")
            return False
    
    async def should_evict(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Determine eviction based on semantic similarity."""
        query = metadata.get('query', '')
        if not query or key not in self.cached_queries:
            return True
        
        try:
            embedding = self.cached_queries[key]
            
            # Find similar cached queries
            D, I = self.index.search(
                np.array([embedding]).astype('float32'),
                min(5, len(self.cached_queries))
            )
            
            # Evict if many similar queries are cached
            return len(D) > 0 and D[0][0] < 0.3
        except Exception as e:
            logging.error(f"Error in semantic eviction decision: {e}")
            return True
    
    async def get_priority(self, key: str, metadata: Dict[str, Any]) -> float:
        """Calculate priority based on semantic uniqueness."""
        query = metadata.get('query', '')
        if not query or key not in self.cached_queries:
            return 0.0
        
        try:
            embedding = self.cached_queries[key]
            
            # Calculate average distance to other cached queries
            D, _ = self.index.search(
                np.array([embedding]).astype('float32'),
                min(10, len(self.cached_queries))
            )
            
            # Higher priority for unique queries
            return float(np.mean(D)) if len(D) > 0 else 1.0
        except Exception as e:
            logging.error(f"Error calculating semantic priority: {e}")
            return 0.0

class HybridCacheStrategy(CacheStrategy):
    """Combines multiple cache strategies with weights."""
    
    def __init__(self):
        self.predictive = PredictiveCacheStrategy()
        self.semantic = SemanticCacheStrategy()
        self.weights = {
            'predictive': 0.5,
            'semantic': 0.5
        }
    
    async def should_cache(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Combine multiple strategies for cache decision."""
        try:
            predictive_score = float(await self.predictive.should_cache(key, metadata))
            semantic_score = float(await self.semantic.should_cache(key, metadata))
            
            combined_score = (
                self.weights['predictive'] * predictive_score +
                self.weights['semantic'] * semantic_score
            )
            
            return combined_score >= 0.5
        except Exception as e:
            logging.error(f"Error in hybrid cache decision: {e}")
            return False
    
    async def should_evict(self, key: str, metadata: Dict[str, Any]) -> bool:
        """Combine multiple strategies for eviction decision."""
        try:
            predictive_score = float(await self.predictive.should_evict(key, metadata))
            semantic_score = float(await self.semantic.should_evict(key, metadata))
            
            combined_score = (
                self.weights['predictive'] * predictive_score +
                self.weights['semantic'] * semantic_score
            )
            
            return combined_score >= 0.5
        except Exception as e:
            logging.error(f"Error in hybrid eviction decision: {e}")
            return True
    
    async def get_priority(self, key: str, metadata: Dict[str, Any]) -> float:
        """Combine multiple strategies for priority calculation."""
        try:
            predictive_priority = await self.predictive.get_priority(key, metadata)
            semantic_priority = await self.semantic.get_priority(key, metadata)
            
            return (
                self.weights['predictive'] * predictive_priority +
                self.weights['semantic'] * semantic_priority
            )
        except Exception as e:
            logging.error(f"Error calculating hybrid priority: {e}")
            return 0.0
    
    async def update_weights(self, 
                           cache_hits: int, 
                           cache_misses: int,
                           strategy_hits: Dict[str, int]) -> None:
        """Dynamically adjust strategy weights based on performance."""
        total_hits = sum(strategy_hits.values())
        if total_hits > 0:
            self.weights = {
                strategy: hits / total_hits
                for strategy, hits in strategy_hits.items()
            }

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