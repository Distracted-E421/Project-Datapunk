from typing import Dict, Any, Optional
import aiohttp
import json
from .framework import LoadTest

class APILoadTest(LoadTest):
    """Load test for API endpoints"""
    
    def __init__(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(f"API_{method}_{endpoint}", **kwargs)
        self.endpoint = endpoint
        self.method = method
        self.payload = payload
        
    async def user_action(self, user_id: int) -> bool:
        """Simulate API request"""
        async with aiohttp.ClientSession() as session:
            try:
                if self.method == "GET":
                    async with session.get(self.endpoint) as response:
                        return response.status == 200
                        
                elif self.method == "POST":
                    async with session.post(
                        self.endpoint,
                        json=self.payload
                    ) as response:
                        return response.status == 200
                        
            except Exception as e:
                self.errors.append(f"Request failed: {str(e)}")
                return False

class DatabaseLoadTest(LoadTest):
    """Load test for database operations"""
    
    def __init__(
        self,
        db_pool,
        query: str,
        params: Optional[tuple] = None,
        **kwargs
    ):
        super().__init__("DB_" + query.split()[0], **kwargs)
        self.db_pool = db_pool
        self.query = query
        self.params = params or tuple()
        
    async def user_action(self, user_id: int) -> bool:
        """Execute database query"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(self.query, *self.params)
                return True
        except Exception as e:
            self.errors.append(f"Query failed: {str(e)}")
            return False

class CacheLoadTest(LoadTest):
    """Load test for cache operations"""
    
    def __init__(
        self,
        redis_client,
        operation: str = "get",
        key_pattern: str = "test:{user}:{id}",
        value: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(f"Cache_{operation}", **kwargs)
        self.redis = redis_client
        self.operation = operation
        self.key_pattern = key_pattern
        self.value = value
        
    async def user_action(self, user_id: int) -> bool:
        """Execute cache operation"""
        try:
            key = self.key_pattern.format(
                user=user_id,
                id=len(self.results)
            )
            
            if self.operation == "get":
                await self.redis.get(key)
                return True
                
            elif self.operation == "set":
                value = self.value or f"test_value_{user_id}"
                await self.redis.set(key, json.dumps(value))
                return True
                
        except Exception as e:
            self.errors.append(f"Cache operation failed: {str(e)}")
            return False 