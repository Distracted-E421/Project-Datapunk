from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging

from ..query.federation.manager import FederationManager
from ..query.federation.monitoring import FederationMonitor
from ..query.federation.visualization import FederationVisualizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/federation", tags=["federation"])

class FederationQuery(BaseModel):
    """Federation query model"""
    query_type: str
    sources: List[str]
    parameters: Dict[str, Any]

class FederationResponse(BaseModel):
    """Federation response model"""
    query_id: str
    status: str
    results: Any
    metadata: Dict[str, Any]

def init_federation_routes(
    federation_manager: FederationManager,
    monitor: FederationMonitor,
    visualizer: FederationVisualizer
):
    """Initialize federation routes with dependencies"""
    
    @router.post("/query", response_model=FederationResponse)
    async def execute_federated_query(query: FederationQuery):
        """Execute a federated query across data sources"""
        try:
            query_id = await federation_manager.execute_query(
                query.query_type,
                query.sources,
                query.parameters
            )
            
            status = await monitor.get_query_status(query_id)
            results = await federation_manager.get_results(query_id)
            
            return FederationResponse(
                query_id=query_id,
                status=status['state'],
                results=results,
                metadata=status['metadata']
            )
        except Exception as e:
            logger.error(f"Federation query failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/status/{query_id}")
    async def get_query_status(query_id: str):
        """Get status of a federated query"""
        try:
            return await monitor.get_query_status(query_id)
        except Exception as e:
            logger.error(f"Failed to get status for query {query_id}: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))

    @router.get("/sources")
    async def list_data_sources():
        """List available federated data sources"""
        try:
            return await federation_manager.list_sources()
        except Exception as e:
            logger.error(f"Failed to list data sources: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/metrics")
    async def get_federation_metrics():
        """Get federation system metrics"""
        try:
            return await monitor.get_metrics()
        except Exception as e:
            logger.error(f"Failed to get federation metrics: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/topology")
    async def get_federation_topology():
        """Get federation topology visualization"""
        try:
            return await visualizer.get_topology()
        except Exception as e:
            logger.error(f"Failed to get federation topology: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/performance")
    async def get_performance_metrics():
        """Get detailed performance metrics"""
        try:
            return await monitor.get_performance_metrics()
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router 