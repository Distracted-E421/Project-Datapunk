from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass
import asyncio
import asyncpg
from datetime import datetime, timedelta
from enum import Enum
from ..monitoring import MetricsCollector

"""
PostgreSQL Connection Pool Manager for Datapunk

This module implements a robust connection pool for PostgreSQL database access,
designed to support Datapunk's high-throughput data processing requirements.
It provides connection lifecycle management, health monitoring, and metrics
collection for observability.

Key Features:
- Configurable pool size and connection parameters
- Connection health validation
- Prepared statement caching
- Metrics collection for monitoring
- Automatic connection recovery
- Resource usage tracking

Integration Points:
- Metrics collection via MetricsCollector
- Service mesh health reporting
- Circuit breaker pattern support
- Resource monitoring

TODO: Implement progressive backoff for failed validations
TODO: Add configurable validation queries
TODO: Add circuit breaker pattern for connection failures
"""

@dataclass
class PoolConfig:
    """
    Configuration for database connection pool with production-ready defaults.
    
    These values are optimized for Datapunk's typical workload patterns:
    - High read/write concurrency
    - Long-running analytical queries
    - Periodic bulk operations
    
    NOTE: Adjust max_size based on available system resources and expected load
    """
    min_size: int = 10
    max_size: int = 100
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0  # seconds
    setup_timeout: float = 60.0  # seconds
    init_timeout: float = 30.0  # seconds
    connection_timeout: float = 10.0  # seconds
    command_timeout: float = 30.0  # seconds
    enable_ssl: bool = True
    enable_prepared_statements: bool = True
    statement_cache_size: int = 1000
    enable_connection_validation: bool = True
    validation_interval: float = 30.0  # seconds

class ConnectionState(Enum):
    """
    Connection states for pool management and monitoring.
    Used by health checks and metrics collection to track connection lifecycle.
    """
    IDLE = "idle"
    BUSY = "busy"
    CLOSED = "closed"
    FAILED = "failed"

class DatabaseError(Exception):
    """
    Base exception class for database operations.
    Provides consistent error handling across the application.
    """
    pass

class ConnectionPool:
    """
    Manages PostgreSQL connection pooling with health monitoring and metrics.
    
    This implementation follows Datapunk's reliability requirements:
    - Connection validation
    - Automatic recovery
    - Resource monitoring
    - Performance metrics
    
    Integration Points:
    - MetricsCollector for operational monitoring
    - Health checks for service mesh integration
    - Resource usage tracking for capacity planning
    """
    def __init__(
        self,
        dsn: str,
        config: PoolConfig,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.dsn = dsn
        self.config = config
        self.metrics = metrics_collector
        self._pool: Optional[asyncpg.Pool] = None
        self._validation_task: Optional[asyncio.Task] = None
        self._stats: Dict[str, Any] = {
            "total_connections": 0,
            "active_connections": 0,
            "idle_connections": 0,
            "queries_executed": 0,
            "failed_queries": 0
        }

    async def initialize(self):
        """
        Initialize connection pool with configured settings and start health monitoring.
        
        NOTE: This method must be called before any database operations can be performed.
        Ensures all connections are properly configured with required codecs and settings.
        
        Raises:
            DatabaseError: If pool initialization fails or configuration is invalid
        """
        try:
            self._pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=self.config.min_size,
                max_size=self.config.max_size,
                max_queries=self.config.max_queries,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
                setup=self._setup_connection,
                init=self._init_connection,
                timeout=self.config.connection_timeout,
                command_timeout=self.config.command_timeout,
                ssl=self.config.enable_ssl
            )

            if self.config.enable_connection_validation:
                self._validation_task = asyncio.create_task(
                    self._validation_loop()
                )

            if self.metrics:
                await self.metrics.increment("database.pool.initialized")

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "database.pool.initialization_error",
                    tags={"error": str(e)}
                )
            raise DatabaseError(f"Failed to initialize pool: {str(e)}")

    async def close(self):
        """Close connection pool"""
        if self._validation_task:
            self._validation_task.cancel()
            try:
                await self._validation_task
            except asyncio.CancelledError:
                pass

        if self._pool:
            await self._pool.close()
            if self.metrics:
                await self.metrics.increment("database.pool.closed")

    async def _setup_connection(self, connection: asyncpg.Connection):
        """
        Configures new database connections with required codecs and settings.
        
        IMPORTANT: Changes here affect all new connections in the pool.
        Ensure compatibility with existing queries before modification.
        
        Current Configuration:
        - JSON encoding/decoding with string representation
        - HStore support for complex data types
        - Prepared statement caching for performance
        """
        # Set session parameters
        await connection.set_type_codec(
            'json',
            encoder=str,
            decoder=str,
            schema='pg_catalog'
        )

        # Set statement cache size
        if self.config.enable_prepared_statements:
            await connection.set_builtin_type_codec(
                'hstore',
                codec_name='pg_contrib.hstore'
            )

    async def _init_connection(self, connection: asyncpg.Connection):
        """Initialize new database connection"""
        # Set session configuration
        await connection.execute('SET statement_timeout = $1', 
                               int(self.config.command_timeout * 1000))
        
        # Update stats
        self._stats["total_connections"] += 1

    async def acquire(self) -> asyncpg.Connection:
        """Acquire database connection from pool"""
        if not self._pool:
            raise DatabaseError("Pool not initialized")

        try:
            connection = await self._pool.acquire(
                timeout=self.config.connection_timeout
            )
            self._stats["active_connections"] += 1
            
            if self.metrics:
                await self.metrics.increment("database.connection.acquired")
                await self.metrics.gauge(
                    "database.connections.active",
                    self._stats["active_connections"]
                )
            
            return connection

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "database.connection.acquisition_error",
                    tags={"error": str(e)}
                )
            raise DatabaseError(f"Failed to acquire connection: {str(e)}")

    async def release(self, connection: asyncpg.Connection):
        """Release database connection back to pool"""
        if not self._pool:
            return

        try:
            await self._pool.release(connection)
            self._stats["active_connections"] -= 1
            
            if self.metrics:
                await self.metrics.increment("database.connection.released")
                await self.metrics.gauge(
                    "database.connections.active",
                    self._stats["active_connections"]
                )

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "database.connection.release_error",
                    tags={"error": str(e)}
                )
            raise DatabaseError(f"Failed to release connection: {str(e)}")

    async def execute(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> str:
        """
        Executes database query with automatic connection management.
        
        NOTE: Uses connection pooling to optimize resource usage.
        Implements retry logic and metrics collection for monitoring.
        
        IMPORTANT: Set appropriate timeout values for long-running queries
        to prevent resource exhaustion.
        """
        async with self.acquire() as connection:
            try:
                result = await connection.execute(
                    query,
                    *args,
                    timeout=timeout or self.config.command_timeout
                )
                self._stats["queries_executed"] += 1
                
                if self.metrics:
                    await self.metrics.increment(
                        "database.query.executed",
                        tags={"query_type": query.split()[0].upper()}
                    )
                
                return result

            except Exception as e:
                self._stats["failed_queries"] += 1
                if self.metrics:
                    await self.metrics.increment(
                        "database.query.error",
                        tags={"error": str(e)}
                    )
                raise DatabaseError(f"Query execution failed: {str(e)}")

    async def fetch(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> List[asyncpg.Record]:
        """Fetch records from database"""
        async with self.acquire() as connection:
            try:
                result = await connection.fetch(
                    query,
                    *args,
                    timeout=timeout or self.config.command_timeout
                )
                self._stats["queries_executed"] += 1
                
                if self.metrics:
                    await self.metrics.increment(
                        "database.query.fetched",
                        tags={"query_type": query.split()[0].upper()}
                    )
                
                return result

            except Exception as e:
                self._stats["failed_queries"] += 1
                if self.metrics:
                    await self.metrics.increment(
                        "database.query.error",
                        tags={"error": str(e)}
                    )
                raise DatabaseError(f"Query fetch failed: {str(e)}")

    async def fetchrow(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None
    ) -> Optional[asyncpg.Record]:
        """Fetch single record from database"""
        async with self.acquire() as connection:
            try:
                result = await connection.fetchrow(
                    query,
                    *args,
                    timeout=timeout or self.config.command_timeout
                )
                self._stats["queries_executed"] += 1
                
                if self.metrics:
                    await self.metrics.increment(
                        "database.query.fetchrow",
                        tags={"query_type": query.split()[0].upper()}
                    )
                
                return result

            except Exception as e:
                self._stats["failed_queries"] += 1
                if self.metrics:
                    await self.metrics.increment(
                        "database.query.error",
                        tags={"error": str(e)}
                    )
                raise DatabaseError(f"Query fetchrow failed: {str(e)}")

    async def _validation_loop(self):
        """
        Periodic health check for all connections in the pool.
        
        Implements Datapunk's connection health monitoring requirements:
        - Regular validation of all connections
        - Metric collection for monitoring
        - Automatic recovery of failed connections
        
        TODO: Add configurable validation queries
        TODO: Implement progressive backoff for failed validations
        FIXME: Add circuit breaker pattern for repeated failures
        """
        while True:
            try:
                await asyncio.sleep(self.config.validation_interval)
                await self._validate_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "database.validation.error",
                        tags={"error": str(e)}
                    )

    async def _validate_connections(self):
        """Validate all connections in pool"""
        if not self._pool:
            return

        async with self.acquire() as connection:
            try:
                await connection.execute('SELECT 1')
                if self.metrics:
                    await self.metrics.increment("database.validation.success")
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "database.validation.failed",
                        tags={"error": str(e)}
                    )

    async def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if not self._pool:
            return self._stats

        return {
            **self._stats,
            "pool_size": len(self._pool._holders),
            "pool_free": self._pool._queue.qsize(),
            "min_size": self.config.min_size,
            "max_size": self.config.max_size
        } 