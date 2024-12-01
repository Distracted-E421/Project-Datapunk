from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import logging

from ..mesh.mesh_integrator import MeshIntegrator
from ..storage.index.strategies.partitioning.base.manager import GridPartitionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/partition", tags=["partition"])

class PartitionHealth(BaseModel):
    """Partition health status model"""
    id: str
    status: str
    timestamp: datetime
    metrics: Dict[str, Any]

class PartitionQuery(BaseModel):
    """Partition query model"""
    query_type: str
    parameters: Dict[str, Any]

class PartitionResponse(BaseModel):
    """Partition response model"""
    partition_id: str
    data: Any
    metadata: Dict[str, Any]

def init_partition_routes(mesh_integrator: MeshIntegrator, partition_manager: GridPartitionManager):
    """Initialize partition routes with dependencies"""
    
    @router.get("/{partition_id}/health", response_model=PartitionHealth)
    async def check_partition_health(partition_id: str):
        """Health check endpoint for specific partition"""
        try:
            health = await mesh_integrator.check_partition_health(partition_id)
            return PartitionHealth(
                id=partition_id,
                status=health['status'],
                timestamp=datetime.fromisoformat(health['timestamp']),
                metrics=health['metrics']
            )
        except Exception as e:
            logger.error(f"Health check failed for partition {partition_id}: {str(e)}")
            raise HTTPException(status_code=503, detail=str(e))

    @router.post("/{partition_id}/query", response_model=PartitionResponse)
    async def handle_partition_query(partition_id: str, query: PartitionQuery):
        """Handle queries for specific partition"""
        try:
            # Validate partition exists and is healthy
            health = await mesh_integrator.check_partition_health(partition_id)
            if health['status'] != 'passing':
                raise HTTPException(
                    status_code=503,
                    detail=f"Partition {partition_id} is not healthy"
                )
            
            # Process query based on type
            result = await partition_manager.execute_query(
                partition_id,
                query.query_type,
                query.parameters
            )
            
            return PartitionResponse(
                partition_id=partition_id,
                data=result,
                metadata={
                    'timestamp': datetime.utcnow().isoformat(),
                    'query_type': query.query_type
                }
            )
        except Exception as e:
            logger.error(f"Query failed for partition {partition_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/list", response_model=List[PartitionHealth])
    async def list_partitions():
        """List all active partitions and their health status"""
        try:
            partitions = await mesh_integrator.list_active_partitions()
            return [
                PartitionHealth(
                    id=p['id'],
                    status=p['health'],
                    timestamp=datetime.utcnow(),
                    metrics=p['meta']
                )
                for p in partitions
            ]
        except Exception as e:
            logger.error(f"Failed to list partitions: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router 