from typing import Any, Dict, Optional, List
import redis
import json
import hashlib
from datetime import timedelta
import asyncio
from functools import lru_cache

class CacheManager:
    """Multi-level cache implementation for Datapunk Cortex"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize Redis connection
        self.redis = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 0),
            decode_responses=True
        )
        
        # Initialize in-memory LRU cache
        self.memory_cache = lru_cache(
            maxsize=config.get('memory_cache_size', 1000)
        )(self._get_cache_value)
        
        # Cache configuration
        self.default_ttl = config.get('default_ttl', 3600)  # 1 hour default
        self.cache_levels = config.get('cache_levels', ['memory', 'redis'])

    def _generate_cache_key(self, data: Dict[str, Any]) -> str:
        """Generate a deterministic cache key from input data"""
        # Sort dictionary to ensure consistent key generation
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    async def get(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from cache, checking multiple levels"""
        cache_key = self._generate_cache_key(input_data)
        
        # Check memory cache first
        if 'memory' in self.cache_levels:
            memory_result = self.memory_cache(cache_key)
            if memory_result:
                return memory_result
        
        # Check Redis cache
        if 'redis' in self.cache_levels:
            redis_result = await self._get_from_redis(cache_key)
            if redis_result:
                # Warm up memory cache
                self.memory_cache(cache_key, redis_result)
                return redis_result
        
        return None

    def _get_cache_value(self, key: str) -> Optional[Dict[str, Any]]:
        """Helper method for LRU cache implementation"""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
        except:
            return None
        return None

    async def _get_from_redis(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from Redis cache"""
        try:
            value = await asyncio.to_thread(self.redis.get, key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"Redis cache error: {e}")
            return None
        return None

    async def set(self, input_data: Dict[str, Any], result: Dict[str, Any], 
                  ttl: Optional[int] = None) -> None:
        """Store data in cache with optional TTL"""
        cache_key = self._generate_cache_key(input_data)
        ttl = ttl or self.default_ttl
        
        try:
            # Store in Redis
            if 'redis' in self.cache_levels:
                serialized = json.dumps(result)
                await asyncio.to_thread(
                    self.redis.setex,
                    cache_key,
                    timedelta(seconds=ttl),
                    serialized
                )
            
            # Update memory cache
            if 'memory' in self.cache_levels:
                self.memory_cache(cache_key, result)
                
        except Exception as e:
            print(f"Cache set error: {e}")

    async def invalidate(self, input_data: Dict[str, Any]) -> None:
        """Invalidate cache entry across all levels"""
        cache_key = self._generate_cache_key(input_data)
        
        # Clear from Redis
        if 'redis' in self.cache_levels:
            await asyncio.to_thread(self.redis.delete, cache_key)
        
        # Clear from memory cache
        if 'memory' in self.cache_levels:
            self.memory_cache.cache_clear()

    async def warm_up(self, common_queries: List[Dict[str, Any]]) -> None:
        """Predictive cache warming for common queries"""
        for query in common_queries:
            cache_key = self._generate_cache_key(query)
            result = await self._get_from_redis(cache_key)
            if result:
                self.memory_cache(cache_key, result) 