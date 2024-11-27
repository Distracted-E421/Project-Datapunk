from typing import Optional, Dict, Any
import asyncpg
from asyncpg import Pool
import time  # Required for health check latency calculation
from .utils.retry import with_retry, RetryConfig

class DatabasePool:
    """Manages PostgreSQL connection pooling with retry logic and health monitoring
    
    This class serves as the primary database interface for the Datapunk system,
    providing connection pooling, automatic retries, and health monitoring capabilities.
    It's designed to be resilient against temporary network issues and provide
    insights into database performance and connection status.
    
    NOTE: This implementation assumes PostgreSQL as the backend database
    TODO: Add support for connection encryption and SSL certificates
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize database pool configuration
        
        Args:
            config: Dictionary containing database connection parameters and pool settings
                   Required keys: host, port, user, password, database
                   Optional keys: min_connections, max_connections, command_timeout,
                                max_queries, max_cached_statement_lifetime,
                                max_cached_statements
        """
        self.config = config
        self.pool: Optional[Pool] = None
        # Configure retry behavior for transient database errors
        self.retry_config = RetryConfig(
            max_attempts=5,  # Balance between reliability and response time
            base_delay=1.0,  # Start with 1 second delay
            max_delay=30.0   # Cap maximum delay to prevent excessive waiting
        )
    
    @with_retry(exceptions=(asyncpg.PostgresError,))
    async def initialize(self) -> None:
        """Initialize connection pool with retry logic
        
        FIXME: Add proper error propagation for configuration issues
        NOTE: Pool creation is separate from __init__ to allow async initialization
        """
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
        """Gracefully close connection pool
        
        NOTE: This should be called during application shutdown
        """
        if self.pool:
            await self.pool.close()
    
    @with_retry(exceptions=(asyncpg.PostgresError,))
    async def execute(self, query: str, *args, **kwargs) -> Any:
        """Execute database query with automatic retry on failure
        
        Args:
            query: SQL query string
            *args: Positional arguments for query parameters
            **kwargs: Keyword arguments for query parameters
        
        Raises:
            RuntimeError: If pool is not initialized
            asyncpg.PostgresError: If query execution fails after retries
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args, **kwargs)
    
    @with_retry(exceptions=(asyncpg.PostgresError,))
    async def fetch(self, query: str, *args, **kwargs) -> list:
        """Fetch query results with automatic retry on failure
        
        Args:
            query: SQL query string
            *args: Positional arguments for query parameters
            **kwargs: Keyword arguments for query parameters
        
        Returns:
            List of query results
            
        Raises:
            RuntimeError: If pool is not initialized
            asyncpg.PostgresError: If query execution fails after retries
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
            
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args, **kwargs)
    
    async def check_health(self) -> Dict[str, Any]:
        """Check database connectivity and return health metrics
        
        Returns:
            Dictionary containing:
                - status: "healthy" or "unhealthy"
                - latency: Query response time in seconds
                - connections: Pool statistics (used/available/max)
                - error: Error message if status is "unhealthy"
        
        TODO: Add configurable timeout for health check query
        NOTE: Connection metrics are important for monitoring pool efficiency
        """
        try:
            if not self.pool:
                return {
                    "status": "unhealthy",
                    "error": "Database pool not initialized"
                }
                
            async with self.pool.acquire() as conn:
                start = time.time()
                # Simple query to verify database responsiveness
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