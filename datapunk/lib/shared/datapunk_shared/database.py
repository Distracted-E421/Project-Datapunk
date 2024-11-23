from typing import Optional, Dict, Any
import asyncpg
from asyncpg import Pool
from .utils.retry import with_retry, RetryConfig

class DatabasePool:
    """Manages database connections with retry logic"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool: Optional[Pool] = None
        self.retry_config = RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            max_delay=30.0
        )
    
    @with_retry(exceptions=(asyncpg.PostgresError,))
    async def initialize(self) -> None:
        """Initialize connection pool with retry logic"""
        self.pool = await asyncpg.create_pool(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['user'],
            password=self.config['password'],
            database=self.config['database'],
            min_size=self.config.get('min_connections', 10),
            max_size=self.config.get('max_connections', 100),
            command_timeout=self.config.get('command_timeout', 60.0),
            max_queries=self.config.get('max_queries', 50000),
            max_cached_statement_lifetime=self.config.get('max_cached_statement_lifetime', 300),
            max_cached_statements=self.config.get('max_cached_statements', 1000)
        )
    
    async def close(self) -> None:
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
    
    @with_retry(exceptions=(asyncpg.PostgresError,))
    async def execute(self, query: str, *args, **kwargs) -> Any:
        """Execute query with retry logic"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args, **kwargs)
    
    @with_retry(exceptions=(asyncpg.PostgresError,))
    async def fetch(self, query: str, *args, **kwargs) -> list:
        """Fetch query results with retry logic"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args, **kwargs)
    
    async def check_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            if not self.pool:
                return {
                    "status": "unhealthy",
                    "error": "Database pool not initialized"
                }
                
            async with self.pool.acquire() as conn:
                start = time.time()
                await conn.execute("SELECT 1")
                latency = time.time() - start
                
                return {
                    "status": "healthy",
                    "latency": latency,
                    "connections": {
                        "used": len(self.pool._holders) - len(self.pool._free),
                        "available": len(self.pool._free),
                        "max": self.pool._maxsize
                    }
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            } 