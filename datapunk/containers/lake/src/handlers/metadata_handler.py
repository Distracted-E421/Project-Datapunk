from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from datetime import datetime

from ..metadata.core import MetadataCore
from ..metadata.store import MetadataStore
from ..metadata.analyzer import MetadataAnalyzer
from ..metadata.cache import MetadataCache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metadata", tags=["metadata"])

class MetadataQuery(BaseModel):
    """Metadata query model"""
    entity_type: str
    filters: Dict[str, Any] = {}
    include_history: bool = False

class MetadataUpdate(BaseModel):
    """Metadata update model"""
    entity_type: str
    entity_id: str
    metadata: Dict[str, Any]
    version: Optional[int] = None

class AnalysisRequest(BaseModel):
    """Metadata analysis request model"""
    entity_type: str
    analysis_type: str
    parameters: Optional[Dict[str, Any]] = None

def init_metadata_routes(
    core: MetadataCore,
    store: MetadataStore,
    analyzer: MetadataAnalyzer,
    cache: MetadataCache
):
    """Initialize metadata routes with dependencies"""

    @router.get("/entities/{entity_type}/{entity_id}")
    async def get_metadata(
        entity_type: str,
        entity_id: str,
        include_history: bool = False
    ):
        """Get metadata for an entity"""
        try:
            metadata = await store.get_metadata(
                entity_type=entity_type,
                entity_id=entity_id,
                include_history=include_history
            )
            
            if not metadata:
                raise HTTPException(
                    status_code=404,
                    detail=f"Metadata not found for {entity_type}/{entity_id}"
                )
            
            return metadata
        except Exception as e:
            logger.error(f"Failed to get metadata: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/entities/search")
    async def search_metadata(query: MetadataQuery):
        """Search metadata based on filters"""
        try:
            results = await store.search_metadata(
                entity_type=query.entity_type,
                filters=query.filters,
                include_history=query.include_history
            )
            
            return {
                'results': results,
                'total': len(results),
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Metadata search failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.put("/entities/{entity_type}/{entity_id}")
    async def update_metadata(
        entity_type: str,
        entity_id: str,
        update: MetadataUpdate
    ):
        """Update metadata for an entity"""
        try:
            if update.entity_type != entity_type or update.entity_id != entity_id:
                raise HTTPException(
                    status_code=400,
                    detail="Entity type/id mismatch in path and body"
                )
            
            updated = await core.update_metadata(
                entity_type=entity_type,
                entity_id=entity_id,
                metadata=update.metadata,
                version=update.version
            )
            
            return {
                'status': 'updated',
                'entity_type': entity_type,
                'entity_id': entity_id,
                'version': updated['version'],
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Metadata update failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/analyze")
    async def analyze_metadata(request: AnalysisRequest):
        """Analyze metadata"""
        try:
            analysis_result = await analyzer.analyze(
                entity_type=request.entity_type,
                analysis_type=request.analysis_type,
                parameters=request.parameters
            )
            
            return {
                'analysis_type': request.analysis_type,
                'entity_type': request.entity_type,
                'results': analysis_result,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Metadata analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/schema/{entity_type}")
    async def get_schema(entity_type: str):
        """Get metadata schema for entity type"""
        try:
            schema = await core.get_schema(entity_type)
            
            if not schema:
                raise HTTPException(
                    status_code=404,
                    detail=f"Schema not found for {entity_type}"
                )
            
            return schema
        except Exception as e:
            logger.error(f"Failed to get schema: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/cache/refresh")
    async def refresh_cache(entity_type: str = None):
        """Refresh metadata cache"""
        try:
            await cache.refresh(entity_type)
            return {
                'status': 'refreshed',
                'entity_type': entity_type,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Cache refresh failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/stats")
    async def get_metadata_stats():
        """Get metadata statistics"""
        try:
            return {
                'store': await store.get_stats(),
                'cache': await cache.get_stats(),
                'analyzer': await analyzer.get_stats(),
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get metadata stats: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router 