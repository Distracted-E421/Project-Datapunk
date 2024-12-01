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

from .handlers.partition_handler import init_partition_routes
from .handlers.stream_handler import init_stream_routes
from .handlers.nexus_handler import init_nexus_routes
from .handlers.ingestion_handler import init_ingestion_routes
from .handlers.federation_handler import init_federation_routes

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
        
        logger.info("Lake service initialized successfully")
        yield
    finally:
        # Cleanup on shutdown
        if app_state.mesh_integrator:
            await app_state.mesh_integrator.cleanup()
        if app_state.partition_manager:
            await app_state.partition_manager.cleanup()
        if app_state.ingestion_core:
            await app_state.ingestion_core.cleanup()
        if app_state.federation_manager:
            await app_state.federation_manager.cleanup()
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

# Initialize route handlers
app.include_router(
    init_partition_routes(
        mesh_integrator=Depends(get_mesh_integrator),
        partition_manager=Depends(get_partition_manager)
    )
)
app.include_router(init_stream_routes())
app.include_router(init_nexus_routes())
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
            "federation": await app_state.federation_monitor.check_health()
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