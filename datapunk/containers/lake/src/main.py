# Lake Service: Core data storage and processing service for Datapunk
# Handles vector, timeseries, and spatial data storage operations
# Part of the Core Services layer in the Datapunk architecture

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import logging
from contextlib import asynccontextmanager

from .config.storage_config import StorageConfig
from .mesh.mesh_integrator import MeshIntegrator
from .storage.index.strategies.partitioning.base.manager import GridPartitionManager
from .ingestion.core import IngestionCore
from .ingestion.monitoring import IngestionMonitor
from .query.federation.manager import FederationManager
from .query.federation.monitoring import FederationMonitor
from .query.federation.visualization import FederationVisualizer
from .storage.stores import TimeSeriesStore, SpatialStore, VectorStore
from .storage.cache import CacheManager
from .storage.quorum import QuorumManager
from .query.parser.sql import SQLParser
from .query.parser.nosql import NoSQLParser
from .query.validation.sql import SQLValidator
from .query.validation.nosql import NoSQLValidator
from .query.optimizer.core import QueryOptimizer
from .query.executor.core import QueryExecutor
from .query.executor.streaming import StreamingExecutor
from .processing.validator import DataValidator

from .metadata.core import MetadataCore
from .metadata.store import MetadataStore
from .metadata.analyzer import MetadataAnalyzer
from .metadata.cache import MetadataCache

from .handlers.partition_handler import init_partition_routes
from .handlers.stream_handler import init_stream_routes
from .handlers.nexus_handler import init_nexus_routes
from .handlers.ingestion_handler import init_ingestion_routes
from .handlers.federation_handler import init_federation_routes
from .handlers.query_handler import init_query_routes
from .handlers.storage_handler import init_storage_routes
from .handlers.processing_handler import init_processing_routes
from .handlers.metadata_handler import init_metadata_routes

logger = logging.getLogger(__name__)

# Application state and dependencies
class AppState:
    def __init__(self):
        self.config = StorageConfig()
        self.mesh_integrator = None
        self.partition_manager = None
        self.ingestion_core = None
        self.ingestion_monitor = None
        self.federation_manager = None
        self.federation_monitor = None
        self.federation_visualizer = None
        self.timeseries_store = None
        self.spatial_store = None
        self.vector_store = None
        self.cache_manager = None
        self.quorum_manager = None
        self.sql_parser = None
        self.nosql_parser = None
        self.sql_validator = None
        self.nosql_validator = None
        self.query_optimizer = None
        self.query_executor = None
        self.streaming_executor = None
        self.data_validator = None
        self.metadata_core = None
        self.metadata_store = None
        self.metadata_analyzer = None
        self.metadata_cache = None

app_state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan and dependencies"""
    try:
        # Initialize mesh integrator
        app_state.mesh_integrator = MeshIntegrator(app_state.config)
        await app_state.mesh_integrator.initialize()
        
        # Initialize partition manager
        app_state.partition_manager = GridPartitionManager()
        await app_state.partition_manager.initialize()
        
        # Initialize ingestion components
        app_state.ingestion_core = IngestionCore()
        app_state.ingestion_monitor = IngestionMonitor()
        await app_state.ingestion_core.initialize()
        
        # Initialize federation components
        app_state.federation_manager = FederationManager()
        app_state.federation_monitor = FederationMonitor()
        app_state.federation_visualizer = FederationVisualizer()
        await app_state.federation_manager.initialize()

        # Initialize storage components
        app_state.timeseries_store = TimeSeriesStore()
        app_state.spatial_store = SpatialStore()
        app_state.vector_store = VectorStore()
        app_state.cache_manager = CacheManager()
        app_state.quorum_manager = QuorumManager()
        await app_state.timeseries_store.initialize()
        await app_state.spatial_store.initialize()
        await app_state.vector_store.initialize()
        await app_state.cache_manager.initialize()
        await app_state.quorum_manager.initialize()

        # Initialize query components
        app_state.sql_parser = SQLParser()
        app_state.nosql_parser = NoSQLParser()
        app_state.sql_validator = SQLValidator()
        app_state.nosql_validator = NoSQLValidator()
        app_state.query_optimizer = QueryOptimizer()
        app_state.query_executor = QueryExecutor()
        app_state.streaming_executor = StreamingExecutor()
        await app_state.query_optimizer.initialize()
        await app_state.query_executor.initialize()
        await app_state.streaming_executor.initialize()

        # Initialize processing components
        app_state.data_validator = DataValidator()
        await app_state.data_validator.initialize()

        # Initialize metadata components
        app_state.metadata_core = MetadataCore()
        app_state.metadata_store = MetadataStore()
        app_state.metadata_analyzer = MetadataAnalyzer()
        app_state.metadata_cache = MetadataCache()
        await app_state.metadata_core.initialize()
        await app_state.metadata_store.initialize()
        await app_state.metadata_analyzer.initialize()
        await app_state.metadata_cache.initialize()

        logger.info("Lake service initialized successfully")
        yield
    finally:
        # Cleanup on shutdown
        components = [
            app_state.mesh_integrator,
            app_state.partition_manager,
            app_state.ingestion_core,
            app_state.federation_manager,
            app_state.timeseries_store,
            app_state.spatial_store,
            app_state.vector_store,
            app_state.cache_manager,
            app_state.quorum_manager,
            app_state.query_optimizer,
            app_state.query_executor,
            app_state.streaming_executor,
            app_state.data_validator,
            app_state.metadata_core,
            app_state.metadata_store,
            app_state.metadata_analyzer,
            app_state.metadata_cache
        ]
        
        for component in components:
            if component:
                await component.cleanup()
        
        logger.info("Lake service shutdown complete")

# Initialize FastAPI with service identity for service mesh discovery
app = FastAPI(
    title="DataPunk Lake Service",
    lifespan=lifespan
)

# TODO: Replace wildcard CORS with environment-specific configuration
# SECURITY: Current CORS setup is for development only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # FIXME: Configure from environment variables
    allow_credentials=True,
    allow_methods=["*"],  # FIXME: Restrict to required methods only
    allow_headers=["*"],  # FIXME: Restrict to required headers only
)

# Dependency injection for handlers
async def get_mesh_integrator():
    return app_state.mesh_integrator

async def get_partition_manager():
    return app_state.partition_manager

async def get_ingestion_core():
    return app_state.ingestion_core

async def get_ingestion_monitor():
    return app_state.ingestion_monitor

async def get_federation_manager():
    return app_state.federation_manager

async def get_federation_monitor():
    return app_state.federation_monitor

async def get_federation_visualizer():
    return app_state.federation_visualizer

async def get_timeseries_store():
    return app_state.timeseries_store

async def get_spatial_store():
    return app_state.spatial_store

async def get_vector_store():
    return app_state.vector_store

async def get_cache_manager():
    return app_state.cache_manager

async def get_quorum_manager():
    return app_state.quorum_manager

async def get_sql_parser():
    return app_state.sql_parser

async def get_nosql_parser():
    return app_state.nosql_parser

async def get_sql_validator():
    return app_state.sql_validator

async def get_nosql_validator():
    return app_state.nosql_validator

async def get_query_optimizer():
    return app_state.query_optimizer

async def get_query_executor():
    return app_state.query_executor

async def get_streaming_executor():
    return app_state.streaming_executor

async def get_data_validator():
    return app_state.data_validator

async def get_metadata_core():
    return app_state.metadata_core

async def get_metadata_store():
    return app_state.metadata_store

async def get_metadata_analyzer():
    return app_state.metadata_analyzer

async def get_metadata_cache():
    return app_state.metadata_cache

# Initialize route handlers
app.include_router(
    init_partition_routes(
        mesh_integrator=Depends(get_mesh_integrator),
        partition_manager=Depends(get_partition_manager)
    )
)
app.include_router(
    init_stream_routes(
        timeseries_store=Depends(get_timeseries_store),
        spatial_store=Depends(get_spatial_store)
    )
)
app.include_router(
    init_nexus_routes(
        vector_store=Depends(get_vector_store)
    )
)
app.include_router(
    init_ingestion_routes(
        ingestion_core=Depends(get_ingestion_core),
        monitor=Depends(get_ingestion_monitor)
    )
)
app.include_router(
    init_federation_routes(
        federation_manager=Depends(get_federation_manager),
        monitor=Depends(get_federation_monitor),
        visualizer=Depends(get_federation_visualizer)
    )
)
app.include_router(
    init_query_routes(
        sql_parser=Depends(get_sql_parser),
        nosql_parser=Depends(get_nosql_parser),
        sql_validator=Depends(get_sql_validator),
        nosql_validator=Depends(get_nosql_validator),
        optimizer=Depends(get_query_optimizer),
        executor=Depends(get_query_executor),
        streaming_executor=Depends(get_streaming_executor)
    )
)
app.include_router(
    init_storage_routes(
        timeseries_store=Depends(get_timeseries_store),
        spatial_store=Depends(get_spatial_store),
        vector_store=Depends(get_vector_store),
        cache_manager=Depends(get_cache_manager),
        quorum_manager=Depends(get_quorum_manager)
    )
)
app.include_router(
    init_processing_routes(
        validator=Depends(get_data_validator)
    )
)
app.include_router(
    init_metadata_routes(
        core=Depends(get_metadata_core),
        store=Depends(get_metadata_store),
        analyzer=Depends(get_metadata_analyzer),
        cache=Depends(get_metadata_cache)
    )
)

# Health check endpoint for service mesh integration
@app.get("/health")
async def health_check():
    """Service health check endpoint"""
    try:
        health_status = {
            "status": "healthy",
            "mesh": await app_state.mesh_integrator.check_mesh_health(),
            "partitions": await app_state.partition_manager.check_health(),
            "ingestion": await app_state.ingestion_monitor.check_health(),
            "federation": await app_state.federation_monitor.check_health(),
            "storage": {
                "timeseries": await app_state.timeseries_store.check_health(),
                "spatial": await app_state.spatial_store.check_health(),
                "vector": await app_state.vector_store.check_health(),
                "cache": await app_state.cache_manager.check_health(),
                "quorum": await app_state.quorum_manager.check_health()
            },
            "query": {
                "optimizer": await app_state.query_optimizer.check_health(),
                "executor": await app_state.query_executor.check_health(),
                "streaming": await app_state.streaming_executor.check_health()
            },
            "processing": await app_state.data_validator.check_health(),
            "metadata": {
                "core": await app_state.metadata_core.check_health(),
                "store": await app_state.metadata_store.check_health(),
                "analyzer": await app_state.metadata_analyzer.check_health(),
                "cache": await app_state.metadata_cache.check_health()
            }
        }
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Development server configuration
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # FIXME: Configure from environment