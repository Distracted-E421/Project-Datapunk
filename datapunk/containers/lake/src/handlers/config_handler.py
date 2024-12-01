from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from datetime import datetime

from ..config.config_manager import ConfigManager
from ..config.storage_config import StorageConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["config"])

class ConfigUpdate(BaseModel):
    """Configuration update model"""
    component: str
    settings: Dict[str, Any]
    reason: Optional[str] = None

class StorageConfigUpdate(BaseModel):
    """Storage configuration update model"""
    max_size_gb: Optional[int] = None
    retention_days: Optional[int] = None
    compression_enabled: Optional[bool] = None
    replication_factor: Optional[int] = None
    consistency_level: Optional[str] = None

def init_config_routes(
    config_manager: ConfigManager,
    storage_config: StorageConfig
):
    """Initialize configuration routes with dependencies"""

    @router.get("/components/{component}")
    async def get_component_config(component: str):
        """Get configuration for a component"""
        try:
            config = await config_manager.get_config(component)
            
            if not config:
                raise HTTPException(
                    status_code=404,
                    detail=f"Configuration not found for component: {component}"
                )
            
            return config
        except Exception as e:
            logger.error(f"Failed to get component config: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.put("/components/{component}")
    async def update_component_config(
        component: str,
        update: ConfigUpdate
    ):
        """Update configuration for a component"""
        try:
            if update.component != component:
                raise HTTPException(
                    status_code=400,
                    detail="Component mismatch in path and body"
                )
            
            updated = await config_manager.update_config(
                component=component,
                settings=update.settings,
                reason=update.reason
            )
            
            return {
                'status': 'updated',
                'component': component,
                'settings': updated,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Configuration update failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/storage")
    async def get_storage_config():
        """Get storage configuration"""
        try:
            return await storage_config.get_config()
        except Exception as e:
            logger.error(f"Failed to get storage config: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.put("/storage")
    async def update_storage_config(update: StorageConfigUpdate):
        """Update storage configuration"""
        try:
            current = await storage_config.get_config()
            
            # Update only provided fields
            if update.max_size_gb is not None:
                current['max_size_gb'] = update.max_size_gb
            if update.retention_days is not None:
                current['retention_days'] = update.retention_days
            if update.compression_enabled is not None:
                current['compression_enabled'] = update.compression_enabled
            if update.replication_factor is not None:
                current['replication_factor'] = update.replication_factor
            if update.consistency_level is not None:
                current['consistency_level'] = update.consistency_level
            
            await storage_config.update_config(current)
            
            return {
                'status': 'updated',
                'config': current,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Storage configuration update failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/validate")
    async def validate_config(component: str = None):
        """Validate configuration"""
        try:
            validation_result = await config_manager.validate_config(component)
            return {
                'is_valid': validation_result['is_valid'],
                'issues': validation_result.get('issues', []),
                'component': component,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/history/{component}")
    async def get_config_history(component: str):
        """Get configuration change history"""
        try:
            history = await config_manager.get_config_history(component)
            return {
                'component': component,
                'history': history,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get config history: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/reload")
    async def reload_config(component: str = None):
        """Reload configuration from disk"""
        try:
            await config_manager.reload_config(component)
            return {
                'status': 'reloaded',
                'component': component,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Configuration reload failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router 