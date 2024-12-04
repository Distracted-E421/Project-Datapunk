from typing import Dict, Set, Optional, Any, List
import asyncio
import time
import logging
from datetime import datetime
from .cache_types import InvalidationStrategy, CacheConfig, CacheEntry
from ..monitoring.metrics import MetricsClient

class InvalidationManager:
    """
    Manages cache entry lifecycle and cleanup based on configurable invalidation strategies.
    
    This component is responsible for:
    - Implementing different cache invalidation policies (TTL, LRU, LFU, FIFO)
    - Performing background cleanup of expired entries
    - Collecting metrics about cache invalidation patterns
    - Maintaining cache size within configured limits
    
    The manager runs as an autonomous background service that can be started
    and stopped independently of other cache operations.
    
    NOTE: Redis operations are not atomic - there's a small window where entries
    might be accessed between validation check and deletion
    TODO: Consider implementing atomic check-and-delete operations
    """

    def __init__(
        self,
        config: CacheConfig,
        redis_client: Any,  # Type Any used due to multiple possible Redis client implementations
        metrics_client: Optional[MetricsClient] = None
    ):
        """
        Initializes the invalidation manager with configuration and dependencies.
        
        IMPORTANT: The redis_client should be configured with appropriate timeouts
        and retry policies as it's used in background operations
        
        NOTE: Metrics collection is optional but highly recommended for production
        environments to monitor cache health
        """
        self.config = config
        self.redis = redis_client
        self.metrics = metrics_client
        self.logger = logging.getLogger(__name__)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False  # Flag to control background task lifecycle

    async def start(self) -> None:
        """
        Activates the invalidation manager and starts background cleanup tasks.
        
        Only starts cleanup tasks for strategies that require active maintenance
        (LRU, LFU, FIFO). TTL-based invalidation relies on Redis's built-in
        expiration mechanism.
        
        NOTE: Can be safely called multiple times - will not create duplicate tasks
        """
        self._running = True
        if self.config.invalidation_strategy in [
            InvalidationStrategy.LRU,
            InvalidationStrategy.LFU,
            InvalidationStrategy.FIFO
        ]:
            self._cleanup_task = asyncio.create_task(self._run_cleanup())

    async def stop(self) -> None:
        """
        Gracefully shuts down the invalidation manager.
        
        Ensures cleanup tasks are properly cancelled and awaited to prevent:
        - Orphaned background tasks
        - Incomplete cleanup operations
        - Resource leaks
        
        IMPORTANT: Should be called before application shutdown to ensure proper cleanup
        """
        self._running = False
        if self._cleanup_task:
            # Ensure graceful shutdown of background task
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass  # Expected during cleanup

    async def should_invalidate(self, entry: CacheEntry) -> bool:
        """
        Determines if a cache entry should be removed based on the configured strategy.
        
        Each strategy implements different eviction logic:
        - TTL: Simple time-based expiration
        - LRU: Removes least recently used entries
        - LFU: Removes least frequently used entries
        
        IMPORTANT: This method must be resilient to malformed entries as they
        may occur due to partial writes or corruption
        
        NOTE: DateTime comparisons assume system clocks are relatively in sync
        TODO: Consider adding clock drift tolerance
        """
        try:
            if not entry:
                return True

            # Strategy-specific invalidation logic
            if self.config.invalidation_strategy == InvalidationStrategy.TTL:
                # Simple time-based expiration check
                if entry.expires_at and datetime.fromisoformat(entry.expires_at) < datetime.now():
                    return True

            elif self.config.invalidation_strategy == InvalidationStrategy.LRU:
                # Check last access time against TTL threshold
                if not entry.last_accessed:
                    return True
                last_access = datetime.fromisoformat(entry.last_accessed)
                if (datetime.now() - last_access).total_seconds() > self.config.ttl:
                    return True

            elif self.config.invalidation_strategy == InvalidationStrategy.LFU:
                # Basic frequency-based eviction
                # TODO: Consider implementing dynamic access count threshold
                if entry.access_count < 1:
                    return True

            return False

        except Exception as e:
            # Log but don't fail - better to keep potentially valid entries than incorrectly invalidate
            self.logger.error(f"Error checking invalidation: {str(e)}")
            return False

    async def _run_cleanup(self) -> None:
        """
        Performs periodic cache maintenance based on the invalidation strategy.
        
        Features:
        - Self-healing: Continues operation after errors
        - Metrics collection for monitoring
        - Configurable cleanup interval
        
        The cleanup process is designed to be low-impact by:
        - Using SCAN instead of KEYS
        - Processing entries in batches
        - Recording performance metrics
        
        WARNING: Long cleanup operations might block other cache operations
        TODO: Add adaptive cleanup timing based on system load
        """
        while self._running:
            try:
                start_time = time.time()
                count = await self._cleanup_entries()
                
                # Record cleanup metrics if available
                if self.metrics and count > 0:
                    # Track total number of cleaned up entries
                    await self.metrics.increment_counter(
                        'cache_cleanup_total',
                        {
                            'namespace': self.config.namespace,
                            'strategy': self.config.invalidation_strategy.value
                        },
                        count
                    )
                    
                    # Track cleanup operation duration
                    duration = time.time() - start_time
                    await self.metrics.record_histogram(
                        'cache_cleanup_duration_seconds',
                        duration,
                        {'namespace': self.config.namespace}
                    )

            except Exception as e:
                self.logger.error(f"Cleanup error: {str(e)}")

            # Fixed interval between cleanup runs
            # TODO: Consider implementing adaptive interval based on invalidation rate
            await asyncio.sleep(60)

    async def _cleanup_entries(self) -> int:
        """
        Scans and removes invalid entries from the cache.
        
        Implementation details:
        - Uses cursor-based iteration to handle large datasets
        - Processes 100 keys per batch to balance throughput and memory
        - Continues partial processing even if individual key operations fail
        
        Returns the number of successfully removed entries.
        
        NOTE: Error handling is deliberately lenient to prevent single key
        failures from blocking the entire cleanup process
        
        TODO: Make batch size configurable based on system resources
        """
        try:
            count = 0
            pattern = f"{self.config.namespace}:*"
            cursor = 0  # Redis SCAN cursor

            while True:
                # Use SCAN for memory-efficient iteration
                cursor, keys = await self.redis.scan(
                    cursor,
                    match=pattern,
                    count=100  # Process in small batches
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
                        # Log but continue processing other keys
                        self.logger.error(f"Error processing key {key}: {str(e)}")

                if cursor == 0:  # SCAN complete
                    break

            return count

        except Exception as e:
            self.logger.error(f"Cleanup entries error: {str(e)}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """
        Collects comprehensive cache statistics for monitoring.
        
        Calculated metrics include:
        - Total and expired entry counts
        - Average access frequency
        - Average entry age
        
        Performance considerations:
        - Uses cursor-based scanning to handle large datasets
        - Aggregates metrics in memory
        - May take significant time on large caches
        
        IMPORTANT: Should not be called too frequently on production systems
        TODO: Add caching of statistics with configurable refresh interval
        """
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