# datapunk/containers/lake/src/services/service_manager.py

from typing import Dict, Any, Optional
import grpc
from datetime import datetime
from core.config import get_settings
from core.monitoring import MetricsCollector
from asyncpg import create_pool, Pool
import redis.asyncio as redis
from ..config.storage_config import StorageConfig
from ..storage.stores import VectorStore, TimeSeriesStore, SpatialStore
from ..mesh.mesh_integrator import MeshIntegrator
from datapunk_shared.utils.retry import with_retry, RetryConfig

class ServiceManager:
    def __init__(self):
        self.settings = get_settings()
        self.metrics = MetricsCollector()
        self.mesh_integrator = None
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=15.0
        )
        
    @with_retry(exceptions=(asyncpg.PostgresError, redis.RedisError))
    async def initialize(self, config: Optional[StorageConfig] = None):
        """Initialize all service components with retry logic"""
        self.config = config or StorageConfig()
        self.db_pool: Optional[Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.vector_store: Optional[VectorStore] = None
        self.timeseries_store: Optional[TimeSeriesStore] = None
        self.spatial_store: Optional[SpatialStore] = None
        
        # Initialize PostgreSQL connection pool
        self.db_pool = await create_pool(
            host=self.config.DB_HOST,
            port=self.config.DB_PORT,
            user=self.config.DB_USER,
            password=self.config.DB_PASSWORD,
            database=self.config.DB_NAME
        )
        
        # Initialize Redis connection
        if self.config.ENABLE_CACHE:
            self.redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                decode_responses=True
            )
        
        # Initialize stores
        self.vector_store = VectorStore(self.db_pool)
        self.timeseries_store = TimeSeriesStore(self.db_pool)
        self.spatial_store = SpatialStore(self.db_pool)
        
        # Initialize mesh integration
        self.mesh_integrator = MeshIntegrator(self.config)
        await self.mesh_integrator.initialize()
    
    async def cleanup(self):
        """Cleanup service connections"""
        if self.db_pool:
            await self.db_pool.close()
        if self.redis_client:
            await self.redis_client.close()
    
    async def health_check(self) -> bool:
        """Check service health"""
        try:
            # Check PostgreSQL connection
            async with self.db_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            # Check Redis connection if enabled
            if self.redis_client:
                await self.redis_client.ping()
            
            return True
        except Exception:
            return False
    
    @with_retry(exceptions=(Exception,))
    async def coordinate_services(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinates operations between services with retry logic"""
        try:
            if operation['type'] == 'stream_data':
                return await self.mesh_integrator.handle_stream_data(operation)
            elif operation['type'] == 'nexus_request':
                return await self.mesh_integrator.handle_nexus_request(operation)
            elif operation['type'] == 'vector_processing':
                return await self._coordinate_cortex_service(operation)
            
            raise ValueError(f"Unknown operation type: {operation['type']}")
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }