from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import logging

from ..ingestion.core import IngestionCore
from ..ingestion.monitoring import IngestionMonitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

class IngestionRequest(BaseModel):
    """Ingestion request model"""
    source_type: str
    format_type: str
    metadata: Dict[str, Any]

class IngestionResponse(BaseModel):
    """Ingestion response model"""
    job_id: str
    status: str
    metadata: Dict[str, Any]

class BulkIngestionRequest(BaseModel):
    """Bulk ingestion request model"""
    source_config: Dict[str, Any]
    format_config: Dict[str, Any]
    batch_size: int = 1000

def init_ingestion_routes(ingestion_core: IngestionCore, monitor: IngestionMonitor):
    """Initialize ingestion routes with dependencies"""
    
    @router.post("/ingest", response_model=IngestionResponse)
    async def ingest_data(request: IngestionRequest):
        """Handle single data ingestion request"""
        try:
            job_id = await ingestion_core.start_ingestion(
                request.source_type,
                request.format_type,
                request.metadata
            )
            
            status = await monitor.get_job_status(job_id)
            return IngestionResponse(
                job_id=job_id,
                status=status['state'],
                metadata=status['metadata']
            )
        except Exception as e:
            logger.error(f"Ingestion failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/bulk", response_model=IngestionResponse)
    async def bulk_ingest(request: BulkIngestionRequest):
        """Handle bulk data ingestion request"""
        try:
            job_id = await ingestion_core.start_bulk_ingestion(
                request.source_config,
                request.format_config,
                request.batch_size
            )
            
            status = await monitor.get_job_status(job_id)
            return IngestionResponse(
                job_id=job_id,
                status=status['state'],
                metadata=status['metadata']
            )
        except Exception as e:
            logger.error(f"Bulk ingestion failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/file", response_model=IngestionResponse)
    async def ingest_file(
        file: UploadFile = File(...),
        format_type: str = None
    ):
        """Handle file upload and ingestion"""
        try:
            job_id = await ingestion_core.ingest_file(
                file.filename,
                await file.read(),
                format_type
            )
            
            status = await monitor.get_job_status(job_id)
            return IngestionResponse(
                job_id=job_id,
                status=status['state'],
                metadata=status['metadata']
            )
        except Exception as e:
            logger.error(f"File ingestion failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/status/{job_id}")
    async def get_ingestion_status(job_id: str):
        """Get status of an ingestion job"""
        try:
            status = await monitor.get_job_status(job_id)
            return status
        except Exception as e:
            logger.error(f"Failed to get status for job {job_id}: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))

    @router.get("/metrics")
    async def get_ingestion_metrics():
        """Get ingestion system metrics"""
        try:
            return await monitor.get_metrics()
        except Exception as e:
            logger.error(f"Failed to get ingestion metrics: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router 