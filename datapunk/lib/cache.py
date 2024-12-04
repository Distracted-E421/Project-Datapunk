from typing import Any, Optional, Union
import json
from datetime import datetime, timedelta
import redis.asyncio as redis
from .config import BaseServiceConfig
from .metrics import MetricsCollector

class CacheManager:
    """Unified cache management system for Datapunk services
    
    Provides a consistent interface for distributed caching across services,
    with built-in metrics tracking and error handling. Uses Redis as the
    backend for its pub/sub capabilities and atomic operations.
    
    NOTE: All values are JSON serialized before storage
    TODO: Add support for cache warming and prefetching
    FIXME: Implement cache invalidation patterns for related keys
    """
    
    def __init__(
        self,
        config: BaseServiceConfig,
        metrics: MetricsCollector,
        prefix: str = "datapunk"
    ):
        """Initialize cache manager with configuration
        
        Args:
            config: Service configuration containing Redis settings
            metrics: Metrics collector for cache operations
            prefix: Key prefix to prevent collisions (default: "datapunk")
        """
        self.config = config
        self.metrics = metrics
        self.prefix = prefix
        self.redis: Optional[redis.Redis] = None
        
    async def initialize(self):
        """Initialize Redis connection pool
        
        Establishes connection to Redis and verifies connectivity.
        NOTE: Connection pooling is handled by redis-py internally
        """
        self.redis = redis.Redis(
            host=self.config.REDIS_HOST,
            port=self.config.REDIS_PORT,
            decode_responses=True  # Automatically decode Redis responses
        )
        await self.redis.ping()  # Verify connection
        
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve and deserialize value from cache
        
        Args:
            key: Cache key to retrieve
            
        Returns:
            Deserialized value if found, None otherwise
            
        Raises:
            CacheError: If retrieval fails
            
        NOTE: JSON deserialization may fail for complex objects
        """
        try:
            full_key = f"{self.prefix}:{key}"
            start_time = datetime.now()
            
            value = await self.redis.get(full_key)
            
            # Track cache hit/miss metrics
            self.metrics.track_operation(
                operation_type="cache_get",
                status="success" if value else "miss"
            )
            
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            self.metrics.track_operation(
                operation_type="cache_get",
                status="error"
            )
            raise CacheError(f"Failed to get key {key}: {str(e)}")
            
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ):
        """Store serialized value in cache with optional TTL
        
        Args:
            key: Cache key
            value: Value to store (must be JSON serializable)
            ttl: Time-to-live (seconds or timedelta, optional)
            
        Raises:
            CacheError: If storage fails
            
        NOTE: Large values may impact Redis memory usage
        TODO: Add compression for large values
        """
        try:
            full_key = f"{self.prefix}:{key}"
            json_value = json.dumps(value)
            
            # Convert timedelta to seconds if provided
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
                
            await self.redis.set(full_key, json_value, ex=ttl)
            
            self.metrics.track_operation(
                operation_type="cache_set",
                status="success"
            )
            
        except Exception as e:
            self.metrics.track_operation(
                operation_type="cache_set",
                status="error"
            )
            raise CacheError(f"Failed to set key {key}: {str(e)}")
            
    async def invalidate(self, key: str):
        """Remove key from cache
        
        Args:
            key: Cache key to invalidate
            
        Raises:
            CacheError: If invalidation fails
            
        NOTE: Does not verify key existence before removal
        """
        try:
            full_key = f"{self.prefix}:{key}"
            await self.redis.delete(full_key)
            
            self.metrics.track_operation(
                operation_type="cache_invalidate",
                status="success"
            )
            
        except Exception as e:
            self.metrics.track_operation(
                operation_type="cache_invalidate",
                status="error"
            )
            raise CacheError(f"Failed to invalidate key {key}: {str(e)}")

class CacheError(Exception):
    """Custom exception for cache-related errors
    
    Provides consistent error handling across cache operations
    """
    pass