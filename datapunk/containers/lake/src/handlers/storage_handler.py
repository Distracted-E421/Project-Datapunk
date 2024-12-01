from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import logging
from datetime import datetime

from ..storage.stores import TimeSeriesStore, SpatialStore, VectorStore
from ..storage.cache import CacheManager
from ..storage.quorum import QuorumManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/storage", tags=["storage"])

class StorageStats(BaseModel):
    """Storage statistics model"""
    total_size_bytes: int
    record_count: int
    last_modified: datetime
    metadata: Dict[str, Any]

class CacheConfig(BaseModel):
    """Cache configuration model"""
    strategy: str
    max_size_bytes: int
    ttl_seconds: Optional[int] = None

def init_storage_routes(
    timeseries_store: TimeSeriesStore,
    spatial_store: SpatialStore,
    vector_store: VectorStore,
    cache_manager: CacheManager,
    quorum_manager: QuorumManager
):
    """Initialize storage routes with dependencies"""

    @router.get("/stats", response_model=Dict[str, StorageStats])
    async def get_storage_stats():
        """Get storage statistics for all stores"""
        try:
            return {
                'timeseries': await timeseries_store.get_stats(),
                'spatial': await spatial_store.get_stats(),
                'vector': await vector_store.get_stats()
            }
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/backup")
    async def create_backup(store_type: str):
        """Create a backup of specified store"""
        try:
            if store_type == "timeseries":
                backup_id = await timeseries_store.create_backup()
            elif store_type == "spatial":
                backup_id = await spatial_store.create_backup()
            elif store_type == "vector":
                backup_id = await vector_store.create_backup()
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown store type: {store_type}"
                )

            return {
                'backup_id': backup_id,
                'timestamp': datetime.utcnow(),
                'store_type': store_type
            }
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/restore/{backup_id}")
    async def restore_backup(backup_id: str, store_type: str):
        """Restore from a backup"""
        try:
            if store_type == "timeseries":
                await timeseries_store.restore_backup(backup_id)
            elif store_type == "spatial":
                await spatial_store.restore_backup(backup_id)
            elif store_type == "vector":
                await vector_store.restore_backup(backup_id)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown store type: {store_type}"
                )

            return {
                'status': 'restored',
                'backup_id': backup_id,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Backup restoration failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/cache/configure")
    async def configure_cache(config: CacheConfig):
        """Configure cache settings"""
        try:
            await cache_manager.configure(
                strategy=config.strategy,
                max_size_bytes=config.max_size_bytes,
                ttl_seconds=config.ttl_seconds
            )
            return {
                'status': 'configured',
                'config': config.dict()
            }
        except Exception as e:
            logger.error(f"Cache configuration failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/cache/clear")
    async def clear_cache():
        """Clear all cache entries"""
        try:
            await cache_manager.clear()
            return {
                'status': 'cleared',
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Cache clearing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/quorum/status")
    async def get_quorum_status():
        """Get quorum status across nodes"""
        try:
            return await quorum_manager.get_status()
        except Exception as e:
            logger.error(f"Failed to get quorum status: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/quorum/rebalance")
    async def rebalance_storage():
        """Trigger storage rebalancing across nodes"""
        try:
            rebalance_id = await quorum_manager.start_rebalance()
            return {
                'status': 'rebalancing',
                'rebalance_id': rebalance_id,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Storage rebalancing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/import")
    async def import_data(
        store_type: str,
        file: UploadFile = File(...),
        options: Dict[str, Any] = {}
    ):
        """Import data from file"""
        try:
            if store_type == "timeseries":
                import_id = await timeseries_store.import_data(file, options)
            elif store_type == "spatial":
                import_id = await spatial_store.import_data(file, options)
            elif store_type == "vector":
                import_id = await vector_store.import_data(file, options)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown store type: {store_type}"
                )

            return {
                'status': 'importing',
                'import_id': import_id,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Data import failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router 