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
from .handlers.partition_handler import init_partition_routes
from .handlers.stream_handler import init_stream_routes
from .handlers.nexus_handler import init_nexus_routes

logger = logging.getLogger(__name__)

# Application state and dependencies
class AppState:
    def __init__(self):
        self.config = StorageConfig()
        self.mesh_integrator = None
        self.partition_manager = None

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
        
        logger.info("Lake service initialized successfully")
        yield
    finally:
        # Cleanup on shutdown
        if app_state.mesh_integrator:
            await app_state.mesh_integrator.cleanup()
        if app_state.partition_manager:
            await app_state.partition_manager.cleanup()
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

# Initialize route handlers
app.include_router(
    init_partition_routes(
        mesh_integrator=Depends(get_mesh_integrator),
        partition_manager=Depends(get_partition_manager)
    )
)
app.include_router(init_stream_routes())
app.include_router(init_nexus_routes())

# Health check endpoint for service mesh integration
@app.get("/health")
async def health_check():
    """Service health check endpoint"""
    try:
        health_status = {
            "status": "healthy",
            "mesh": await app_state.mesh_integrator.check_mesh_health(),
            "partitions": await app_state.partition_manager.check_health()
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