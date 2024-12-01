from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import numpy as np

from ..storage.stores import VectorStore
from ..processing.validator import DataValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nexus", tags=["nexus"])

class VectorSearchRequest(BaseModel):
    """Vector search request model"""
    vector: List[float]
    limit: int = 10
    metadata_filters: Dict[str, Any] = {}

class VectorSearchResponse(BaseModel):
    """Vector search response model"""
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]

def init_nexus_routes(vector_store: VectorStore):
    """Initialize nexus routes with dependencies"""
    
    validator = DataValidator()
    
    @router.post("/search", response_model=VectorSearchResponse)
    async def vector_search(request: VectorSearchRequest):
        """Handle vector similarity search request"""
        try:
            # Validate vector before processing
            vector = validator.validate_vector(request.vector)
            
            # Perform similarity search
            results = await vector_store.search_similar(
                vector=vector,
                limit=request.limit,
                filters=request.metadata_filters
            )
            
            return VectorSearchResponse(
                results=results,
                metadata={
                    'total_vectors': await vector_store.get_total_count(),
                    'dimensions': len(request.vector)
                }
            )
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/stats")
    async def get_vector_stats():
        """Get vector store statistics"""
        try:
            return {
                'total_vectors': await vector_store.get_total_count(),
                'index_status': await vector_store.get_index_status(),
                'storage_usage': await vector_store.get_storage_usage()
            }
        except Exception as e:
            logger.error(f"Failed to get vector stats: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router