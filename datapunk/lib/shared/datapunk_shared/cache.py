from typing import Any, Optional, Union
import json
from datetime import datetime, timedelta
import redis.asyncio as redis
from .config import BaseServiceConfig
from .metrics import MetricsCollector

class CacheManager:
    """Unified cache management for services"""
    
    def __init__(
        self,
        config: BaseServiceConfig,
        metrics: MetricsCollector,
        prefix: str = "datapunk"
    ):
        self.config = config
        self.metrics = metrics
        self.prefix = prefix
        self.redis: Optional[redis.Redis] = None
        
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis = redis.Redis(
            host=self.config.REDIS_HOST,
            port=self.config.REDIS_PORT,
            decode_responses=True
        )
        await self.redis.ping()  # Verify connection
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            full_key = f"{self.prefix}:{key}"
            start_time = datetime.now()
            
            value = await self.redis.get(full_key)
            
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
        """Set value in cache"""
        try:
            full_key = f"{self.prefix}:{key}"
            json_value = json.dumps(value)
            
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
        """Invalidate cache key"""
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
    """Cache operation error"""
    pass 