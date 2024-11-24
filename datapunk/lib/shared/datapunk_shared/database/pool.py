from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass
import asyncio
import asyncpg
from datetime import datetime, timedelta
from enum import Enum
from ..monitoring import MetricsCollector

@dataclass
class PoolConfig:
    """Configuration for database connection pool"""
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
    """Connection states"""
    IDLE = "idle"
    BUSY = "busy"
    CLOSED = "closed"
    FAILED = "failed"

class DatabaseError(Exception):
    """Base class for database errors"""
    pass

class ConnectionPool:
    """Manages database connection pooling"""
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
        """Initialize connection pool"""
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
        """Set up new database connection"""
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
        """Execute database query"""
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
        """Periodic connection validation"""
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