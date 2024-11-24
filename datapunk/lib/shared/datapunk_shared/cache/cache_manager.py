from typing import Any, Optional, Dict, List, Set
import asyncio
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import aioredis
from .cache_types import (
    CacheStrategy, InvalidationStrategy, CacheConfig, CacheEntry
)
from ..error.error_types import ServiceError, ErrorCategory, ErrorContext
from ..monitoring.metrics import MetricsClient
from .cluster_manager import ClusterManager, ClusterNode

class CacheManager:
    def __init__(
        self,
        config: CacheConfig,
        redis_url: str,
        metrics_client: Optional[MetricsClient] = None,
        cluster_nodes: Optional[List[ClusterNode]] = None
    ):
        self.config = config
        self.metrics = metrics_client
        self.logger = logging.getLogger(__name__)
        
        # Initialize cluster if nodes provided
        self.cluster = None
        if cluster_nodes:
            self.cluster = ClusterManager(config, cluster_nodes, metrics_client)
            self.redis = None  # Will be set per-operation based on cluster
        else:
            self.redis = aioredis.from_url(redis_url)
        
        self._write_buffer: Dict[str, Any] = {}
        self._write_task: Optional[asyncio.Task] = None

        if self.config.strategy == CacheStrategy.WRITE_BEHIND:
            self._start_write_behind_task()

    async def start(self) -> None:
        """Start cache manager"""
        if self.cluster:
            await self.cluster.start()

    async def stop(self) -> None:
        """Stop cache manager"""
        if self.cluster:
            await self.cluster.stop()
        elif self.redis:
            await self.redis.close()

    async def get(
        self,
        key: str,
        fetch_func: Optional[callable] = None
    ) -> Optional[Any]:
        """Get value from cache with cluster support"""
        try:
            start_time = time.time()
            namespace_key = f"{self.config.namespace}:{key}"

            # Get appropriate Redis connection
            redis_conn = self.redis
            if self.cluster:
                node = await self.cluster.get_node_for_key(namespace_key)
                if not node or not node.connection:
                    raise Exception("No available cache node")
                redis_conn = node.connection

            # Try to get from cache
            cached_data = await redis_conn.get(namespace_key)
            
            if cached_data:
                entry = CacheEntry(**json.loads(cached_data))
                
                # Check expiration
                if entry.expires_at and datetime.fromisoformat(entry.expires_at) < datetime.now():
                    await self.invalidate(key)
                    cached_data = None
                else:
                    # Update access stats
                    entry.access_count += 1
                    entry.last_accessed = datetime.now().isoformat()
                    await redis_conn.set(
                        namespace_key,
                        json.dumps(entry.__dict__),
                        ex=self.config.ttl
                    )
                    
                    if self.metrics:
                        await self.metrics.increment_counter(
                            'cache_hits_total',
                            {'namespace': self.config.namespace}
                        )
                    
                    return entry.value

            # Handle cache miss
            if self.metrics:
                await self.metrics.increment_counter(
                    'cache_misses_total',
                    {'namespace': self.config.namespace}
                )

            if not fetch_func:
                return None

            # Fetch from source
            value = await fetch_func()
            
            if value is not None:
                await self.set(key, value)
            
            return value

        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {str(e)}")
            raise ServiceError(
                code="CACHE_GET_ERROR",
                message=f"Failed to get cache value: {str(e)}",
                category=ErrorCategory.CACHE,
                context=ErrorContext(
                    service_id="cache_manager",
                    operation="get",
                    trace_id="",
                    timestamp=time.time(),
                    additional_data={'key': key}
                )
            )
        finally:
            if self.metrics:
                duration = time.time() - start_time
                await self.metrics.record_histogram(
                    'cache_operation_duration_seconds',
                    duration,
                    {'operation': 'get', 'namespace': self.config.namespace}
                )

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with cluster support"""
        try:
            start_time = time.time()
            namespace_key = f"{self.config.namespace}:{key}"
            
            # Handle write-behind
            if self.config.strategy == CacheStrategy.WRITE_BEHIND:
                self._write_buffer[namespace_key] = value
                return True

            # Get appropriate Redis connection
            redis_conn = self.redis
            if self.cluster:
                node = await self.cluster.get_node_for_key(namespace_key)
                if not node or not node.connection:
                    raise Exception("No available cache node")
                redis_conn = node.connection

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now().isoformat(),
                expires_at=(
                    datetime.now() + timedelta(seconds=ttl or self.config.ttl)
                ).isoformat(),
                metadata={'strategy': self.config.strategy.value}
            )

            # Set in cache
            await redis_conn.set(
                namespace_key,
                json.dumps(entry.__dict__),
                ex=ttl or self.config.ttl
            )

            # Sync across cluster if needed
            if self.cluster:
                await self.cluster.sync_key(namespace_key, entry.__dict__, ttl)

            if self.metrics:
                await self.metrics.increment_counter(
                    'cache_writes_total',
                    {'namespace': self.config.namespace}
                )

            return True

        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {str(e)}")
            raise ServiceError(
                code="CACHE_SET_ERROR",
                message=f"Failed to set cache value: {str(e)}",
                category=ErrorCategory.CACHE,
                context=ErrorContext(
                    service_id="cache_manager",
                    operation="set",
                    trace_id="",
                    timestamp=time.time(),
                    additional_data={'key': key}
                )
            )
        finally:
            if self.metrics:
                duration = time.time() - start_time
                await self.metrics.record_histogram(
                    'cache_operation_duration_seconds',
                    duration,
                    {'operation': 'set', 'namespace': self.config.namespace}
                )

    async def invalidate(self, key: str) -> bool:
        """Invalidate a cache entry"""
        try:
            namespace_key = f"{self.config.namespace}:{key}"
            await self.redis.delete(namespace_key)
            
            if self.metrics:
                await self.metrics.increment_counter(
                    'cache_invalidations_total',
                    {'namespace': self.config.namespace}
                )
            
            return True

        except Exception as e:
            self.logger.error(f"Cache invalidation error for key {key}: {str(e)}")
            return False

    async def clear_namespace(self) -> bool:
        """Clear all entries in the current namespace"""
        try:
            pattern = f"{self.config.namespace}:*"
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor,
                    match=pattern,
                    count=100
                )
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
            return True

        except Exception as e:
            self.logger.error(f"Cache clear error for namespace {self.config.namespace}: {str(e)}")
            return False

    def _start_write_behind_task(self) -> None:
        """Start the write-behind task for batched writes"""
        async def write_behind_worker():
            while True:
                try:
                    if self._write_buffer:
                        buffer_copy = self._write_buffer.copy()
                        self._write_buffer.clear()
                        
                        # Batch write to Redis
                        pipe = self.redis.pipeline()
                        for key, value in buffer_copy.items():
                            entry = CacheEntry(
                                key=key,
                                value=value,
                                created_at=datetime.now().isoformat(),
                                expires_at=(
                                    datetime.now() + timedelta(seconds=self.config.ttl)
                                ).isoformat(),
                                metadata={'strategy': 'write_behind'}
                            )
                            pipe.set(
                                key,
                                json.dumps(entry.__dict__),
                                ex=self.config.ttl
                            )
                        await pipe.execute()
                        
                        if self.metrics:
                            await self.metrics.increment_counter(
                                'cache_batch_writes_total',
                                {'namespace': self.config.namespace}
                            )
                
                except Exception as e:
                    self.logger.error(f"Write-behind task error: {str(e)}")
                
                await asyncio.sleep(self.config.write_interval or 5)

        self._write_task = asyncio.create_task(write_behind_worker())

    async def close(self) -> None:
        """Clean up resources"""
        if self._write_task:
            self._write_task.cancel()
            try:
                await self._write_task
            except asyncio.CancelledError:
                pass
        
        await self.redis.close() 