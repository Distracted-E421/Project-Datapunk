from typing import Dict, Set, Optional, Any, List
import asyncio
import time
import logging
from datetime import datetime
from .cache_types import InvalidationStrategy, CacheConfig, CacheEntry
from ..monitoring.metrics import MetricsClient

class InvalidationManager:
    def __init__(
        self,
        config: CacheConfig,
        redis_client: Any,
        metrics_client: Optional[MetricsClient] = None
    ):
        self.config = config
        self.redis = redis_client
        self.metrics = metrics_client
        self.logger = logging.getLogger(__name__)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the invalidation manager"""
        self._running = True
        if self.config.invalidation_strategy in [
            InvalidationStrategy.LRU,
            InvalidationStrategy.LFU,
            InvalidationStrategy.FIFO
        ]:
            self._cleanup_task = asyncio.create_task(self._run_cleanup())

    async def stop(self) -> None:
        """Stop the invalidation manager"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def should_invalidate(self, entry: CacheEntry) -> bool:
        """Check if an entry should be invalidated"""
        try:
            if not entry:
                return True

            # TTL check
            if self.config.invalidation_strategy == InvalidationStrategy.TTL:
                if entry.expires_at and datetime.fromisoformat(entry.expires_at) < datetime.now():
                    return True

            # LRU check
            elif self.config.invalidation_strategy == InvalidationStrategy.LRU:
                if not entry.last_accessed:
                    return True
                last_access = datetime.fromisoformat(entry.last_accessed)
                if (datetime.now() - last_access).total_seconds() > self.config.ttl:
                    return True

            # LFU check
            elif self.config.invalidation_strategy == InvalidationStrategy.LFU:
                if entry.access_count < 1:  # Configurable threshold
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking invalidation: {str(e)}")
            return False

    async def _run_cleanup(self) -> None:
        """Run periodic cleanup based on invalidation strategy"""
        while self._running:
            try:
                start_time = time.time()
                count = await self._cleanup_entries()
                
                if self.metrics and count > 0:
                    await self.metrics.increment_counter(
                        'cache_cleanup_total',
                        {
                            'namespace': self.config.namespace,
                            'strategy': self.config.invalidation_strategy.value
                        },
                        count
                    )
                    
                    duration = time.time() - start_time
                    await self.metrics.record_histogram(
                        'cache_cleanup_duration_seconds',
                        duration,
                        {'namespace': self.config.namespace}
                    )

            except Exception as e:
                self.logger.error(f"Cleanup error: {str(e)}")

            await asyncio.sleep(60)  # Configurable interval

    async def _cleanup_entries(self) -> int:
        """Clean up invalid entries based on strategy"""
        try:
            count = 0
            pattern = f"{self.config.namespace}:*"
            cursor = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor,
                    match=pattern,
                    count=100
                )

                for key in keys:
                    try:
                        data = await self.redis.get(key)
                        if data:
                            entry = CacheEntry(**data)
                            if await self.should_invalidate(entry):
                                await self.redis.delete(key)
                                count += 1
                    except Exception as e:
                        self.logger.error(f"Error processing key {key}: {str(e)}")

                if cursor == 0:
                    break

            return count

        except Exception as e:
            self.logger.error(f"Cleanup entries error: {str(e)}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get invalidation statistics"""
        try:
            pattern = f"{self.config.namespace}:*"
            stats = {
                'total_entries': 0,
                'expired_entries': 0,
                'avg_access_count': 0,
                'avg_age_seconds': 0
            }
            
            cursor = 0
            total_access_count = 0
            total_age = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor,
                    match=pattern,
                    count=100
                )

                for key in keys:
                    try:
                        data = await self.redis.get(key)
                        if data:
                            entry = CacheEntry(**data)
                            stats['total_entries'] += 1
                            
                            if await self.should_invalidate(entry):
                                stats['expired_entries'] += 1
                            
                            total_access_count += entry.access_count
                            created_at = datetime.fromisoformat(entry.created_at)
                            total_age += (datetime.now() - created_at).total_seconds()
                    except Exception as e:
                        self.logger.error(f"Error processing key {key}: {str(e)}")

                if cursor == 0:
                    break

            if stats['total_entries'] > 0:
                stats['avg_access_count'] = total_access_count / stats['total_entries']
                stats['avg_age_seconds'] = total_age / stats['total_entries']

            return stats

        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            return {} 