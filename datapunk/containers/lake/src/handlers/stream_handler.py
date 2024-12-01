# Stream data processing handler for Lake service
# Manages real-time data ingestion and storage with type-specific processing
# Part of the Core Services layer (see sys-arch.mmd)

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import logging

from ..processing.validator import DataValidator
from ..storage.stores import TimeSeriesStore, SpatialStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["stream"])

class LocationRecord(BaseModel):
    """Location record model"""
    latitude: float
    longitude: float
    timestamp: datetime
    source: str

class LocationHistoryRequest(BaseModel):
    """Location history request model"""
    user_id: str
    records: List[LocationRecord]

class ActivityData(BaseModel):
    """Activity data model"""
    user_id: str
    timestamp: datetime
    metrics: Dict[str, float]
    source: str

class StreamResponse(BaseModel):
    """Stream processing response model"""
    status: str
    processed: int
    timestamp: datetime

def init_stream_routes(timeseries_store: TimeSeriesStore, spatial_store: SpatialStore):
    """Initialize stream routes with dependencies"""
    
    validator = DataValidator()
    
    @router.post("/location", response_model=StreamResponse)
    async def process_location_history(request: LocationHistoryRequest):
        """Handle location history stream data"""
        try:
            processed_count = 0
            
            for record in request.records:
                # Create GeoJSON point
                geom = {
                    'type': 'Point',
                    'coordinates': [record.longitude, record.latitude]
                }
                
                # Store in spatial database
                await spatial_store.insert_location(
                    geom=geom,
                    properties={
                        'user_id': request.user_id,
                        'timestamp': record.timestamp,
                        'source': record.source
                    }
                )
                processed_count += 1
            
            return StreamResponse(
                status='success',
                processed=processed_count,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Location history processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/activity", response_model=StreamResponse)
    async def process_activity_data(data: ActivityData):
        """Handle activity stream data"""
        try:
            # Store in time series database
            await timeseries_store.insert_metrics(
                metrics=data.metrics,
                timestamp=data.timestamp
            )
            
            return StreamResponse(
                status='success',
                processed=1,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Activity data processing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/stats")
    async def get_stream_stats():
        """Get stream processing statistics"""
        try:
            return {
                'location_stats': await spatial_store.get_stats(),
                'activity_stats': await timeseries_store.get_stats(),
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get stream stats: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router 