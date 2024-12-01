from typing import Any, Dict, Optional, Union, List
import asyncio
import logging
from datetime import datetime, timedelta
import aioredis
from enum import Enum
import hashlib
import pickle
from dataclasses import dataclass
from ..ingestion.monitoring import HandlerMetrics, MetricType
from .cache_strategies import (
    EvictionStrategy,
    CacheWarmer,
    DistributedCache,
    StrategyFactory,
    AccessPattern,
    TimeBasedWarming,
    RelatedKeyWarming,
    HybridWarming,
    ReplicationManager,
    EnhancedMetrics,
    MLBasedWarming,
    SeasonalWarming,
    QuorumReplication
)

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    RANDOM = "random"  # Random Eviction
    TTL = "ttl"  # Time To Live

@dataclass
class CacheConfig:
    """Cache configuration settings"""
    strategy: CacheStrategy = CacheStrategy.LRU
    ttl: int = 3600  # Default 1 hour TTL
    max_size: int = 1000  # Maximum number of items
    compression: bool = True
    serializer: str = "json"  # or "pickle" for complex objects
    distributed: bool = False
    nodes: Optional[List[Dict[str, Any]]] = None
    replication_factor: int = 2
    warm_patterns: Optional[Dict[str, Dict]] = None
    warming_strategies: List[str] = ("time", "related", "ml", "seasonal")
    access_pattern_window: int = 3600
    read_quorum: int = 2
    write_quorum: int = 2
    ml_update_interval: int = 3600
    seasonal_threshold: float = 0.7
    probability_threshold: float = 0.7

class Cache:
    """Enhanced cache implementation with advanced warming and quorum replication"""
    
    def __init__(
        self,
        redis: aioredis.Redis,
        config: CacheConfig,
        metrics: HandlerMetrics
    ):
        self.redis = redis
        self.config = config
        self.enhanced_metrics = EnhancedMetrics(metrics)
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Initialize access pattern tracking
        self.access_pattern = AccessPattern(config.access_pattern_window)
        
        # Initialize strategy
        self.strategy = StrategyFactory.create_strategy(
            config.strategy,
            redis
        )
        
        # Initialize distributed cache if configured
        self.distributed = None
        self.replication = None
        if config.distributed and config.nodes:
            self.distributed = DistributedCache(config.nodes)
            self.replication = ReplicationManager(
                config.nodes,
                config.replication_factor
            )
            
        # Initialize quorum replication if configured
        self.quorum = None
        if config.distributed and config.nodes:
            self.quorum = QuorumReplication(
                config.nodes,
                config.read_quorum,
                config.write_quorum
            )
        
        # Initialize warming strategies
        if config.warm_patterns:
            warming_strategies = []
            
            if "time" in config.warming_strategies:
                warming_strategies.append(
                    TimeBasedWarming(redis, self.access_pattern)
                )
                
            if "related" in config.warming_strategies:
                warming_strategies.append(
                    RelatedKeyWarming(redis, self.access_pattern)
                )
                
            if "ml" in config.warming_strategies:
                warming_strategies.append(
                    MLBasedWarming(
                        redis,
                        self.access_pattern,
                        config.ml_update_interval
                    )
                )
                
            if "seasonal" in config.warming_strategies:
                warming_strategies.append(
                    SeasonalWarming(redis, self.access_pattern)
                )
                
            if warming_strategies:
                self.warmer = CacheWarmer(
                    redis,
                    self._fetch_missing,
                    metrics,
                    HybridWarming(warming_strategies)
                )
                
    async def start(self):
        """Start cache management tasks"""
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        if self.warmer:
            await self.warmer.start()
            for pattern, config in self.config.warm_patterns.items():
                await self.warmer.register_pattern(pattern, config)
                
        if self.replication:
            await self.replication.start()
                
        if self.quorum:
            await self.quorum.start()
    
    async def stop(self):
        """Stop cache management tasks"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        if self.warmer:
            await self.warmer.stop()
            
        if self.replication:
            await self.replication.stop()
                
        if self.quorum:
            await self.quorum.stop()
    
    async def get(
        self,
        key: str,
        default: Any = None,
        format: Optional[str] = None
    ) -> Any:
        """Get item from cache with quorum consensus"""
        await self.enhanced_metrics.record_operation_start("get", key)
        success = False
        
        try:
            if self.quorum:
                # Read with quorum consensus
                value, nodes, consistent = await self.quorum.read(key)
                if not value:
                    await self.enhanced_metrics.record_operation_end(
                        "get",
                        key,
                        False,
                        {"reason": "miss"}
                    )
                    return default
                    
                if not consistent:
                    logger.warning(
                        f"Inconsistent values for key {key} across nodes"
                    )
                    
                # Update access patterns
                self.access_pattern.record_access(key)
                await self.strategy.record_access(key)
                
                result = await self._deserialize(
                    value,
                    format or self.config.serializer
                )
                
                success = True
                return result
            else:
                # Single node get
                return await super().get(key, default, format)
                
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return default
            
        finally:
            await self.enhanced_metrics.record_operation_end(
                "get",
                key,
                success,
                {
                    "quorum": bool(self.quorum),
                    "error": str(e) if 'e' in locals() else None
                }
            )
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        format: Optional[str] = None
    ) -> bool:
        """Store item in cache with quorum consensus"""
        await self.enhanced_metrics.record_operation_start("set", key)
        success = False
        
        try:
            # Serialize data
            data = await self._serialize(
                value,
                format or self.config.serializer
            )
            
            if self.quorum:
                # Write with quorum consensus
                success, nodes = await self.quorum.write(key, data, ttl)
                
                # Update strategy metadata
                if success:
                    self.access_pattern.record_access(key)
                    await self.strategy.record_access(key)
                    
                return success
            else:
                # Single node set
                return await super().set(key, value, ttl, format)
                
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
            
        finally:
            await self.enhanced_metrics.record_operation_end(
                "set",
                key,
                success,
                {
                    "quorum": bool(self.quorum),
                    "error": str(e) if 'e' in locals() else None
                }
            )
    
    async def delete(self, key: str) -> bool:
        """Remove item from cache with quorum consensus"""
        await self.enhanced_metrics.record_operation_start("delete", key)
        success = False
        
        try:
            if self.quorum:
                # Delete from all nodes in write quorum
                success, nodes = await self.quorum.write(key, b"", 1)  # TTL=1 for immediate deletion
                
                if success:
                    await self.strategy.remove_key(key)
                    
                return success
            else:
                # Single node delete
                return await super().delete(key)
                
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
            
        finally:
            await self.enhanced_metrics.record_operation_end(
                "delete",
                key,
                success,
                {
                    "quorum": bool(self.quorum),
                    "error": str(e) if 'e' in locals() else None
                }
            )
    
    async def clear(self, namespace: Optional[str] = None) -> int:
        """Clear cache entries"""
        await self.enhanced_metrics.record_operation_start(
            "clear",
            namespace or "all"
        )
        cleared = 0
        success = False
        
        try:
            pattern = f"{namespace}:*" if namespace else "*"
            
            if self.distributed:
                # Clear from all nodes
                for node in self.config.nodes:
                    redis = await aioredis.from_url(
                        f"redis://{node['host']}:{node['port']}"
                    )
                    keys = await redis.keys(pattern)
                    if keys:
                        cleared += await redis.delete(*keys)
            else:
                keys = await self.redis.keys(pattern)
                if keys:
                    cleared = await self.redis.delete(*keys)
                    
            success = True
            return cleared
            
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return 0
            
        finally:
            await self.enhanced_metrics.record_operation_end(
                "clear",
                namespace or "all",
                success,
                {
                    "cleared": cleared,
                    "namespace": namespace or "all"
                }
            )
    
    async def _get_connection(self, key: str) -> aioredis.Redis:
        """Get Redis connection for key"""
        if self.distributed:
            return await self.distributed.get_connection(key)
        return self.redis
    
    async def _serialize(self, data: Any, format: str) -> bytes:
        """Serialize data with compression if enabled"""
        try:
            if format == "json":
                import json
                serialized = json.dumps(data).encode()
            elif format == "pickle":
                serialized = pickle.dumps(data)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            if self.config.compression:
                import zlib
                return zlib.compress(serialized)
            return serialized
        except Exception as e:
            logger.error(f"Serialization error: {str(e)}")
            raise
    
    async def _deserialize(self, data: bytes, format: str) -> Any:
        """Deserialize data with decompression if needed"""
        try:
            if self.config.compression:
                import zlib
                data = zlib.decompress(data)
                
            if format == "json":
                import json
                return json.loads(data.decode())
            elif format == "pickle":
                return pickle.loads(data)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            logger.error(f"Deserialization error: {str(e)}")
            raise
    
    async def _periodic_cleanup(self):
        """Periodic cache maintenance"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self._enforce_max_size()
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {str(e)}")
    
    async def _enforce_max_size(self):
        """Enforce maximum cache size"""
        total_keys = await self.redis.dbsize()
        
        if total_keys > self.config.max_size:
            to_remove = total_keys - self.config.max_size
            keys = await self.strategy.get_eviction_candidates(to_remove)
            
            if keys:
                await self.redis.delete(*keys)
                await self.enhanced_metrics.record_metric(
                    "cache_eviction",
                    len(keys),
                    MetricType.COUNTER,
                    {"strategy": self.config.strategy.value}
                )
    
    async def _cleanup_expired(self):
        """Clean up expired entries and strategy metadata"""
        # Redis handles TTL expiration automatically
        # Clean up strategy metadata
        keys = await self.redis.keys("*")
        for key in keys:
            if not await self.redis.exists(key):
                await self.strategy.remove_key(key)
                
    async def _fetch_missing(self, key: str) -> Optional[Any]:
        """Fetch missing data for cache warming"""
        # Implement your data fetching logic here
        # This should connect to your data source
        return None