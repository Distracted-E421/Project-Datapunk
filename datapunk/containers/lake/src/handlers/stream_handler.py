# Stream data processing handler for Lake service
# Manages real-time data ingestion and storage with type-specific processing
# Part of the Core Services layer (see sys-arch.mmd)

from typing import Dict, Any
from datetime import datetime
import json
from ..processing.validator import DataValidator
from ..storage.stores import TimeSeriesStore, SpatialStore

class StreamHandler:
    """
    Real-time stream data processor with specialized storage handlers
    
    Processes incoming data streams with type-specific handling:
    - Location data → Spatial storage with GeoJSON formatting
    - Activity data → Time series storage with metrics
    
    NOTE: Critical for real-time data sovereignty - enables immediate data control
    FIXME: Add proper error recovery for failed stream processing
    """
    
    def __init__(self, timeseries_store: TimeSeriesStore, spatial_store: SpatialStore):
        # Initialize storage engines for different data types
        self.timeseries_store = timeseries_store
        self.spatial_store = spatial_store
        self.validator = DataValidator()
    
    async def process_stream_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes incoming stream data to appropriate processor based on content type
        Ensures data validation before processing
        """
        try:
            # Validate basic structure before processing
            if 'payload' not in data:
                raise ValueError("Missing payload in stream data")
                
            payload = data['payload']
            
            # Route to specialized processors based on content type
            if payload['data']['content_type'] == 'location_history':
                return await self._process_location_history(payload)
            elif payload['data']['content_type'] == 'activity_data':
                return await self._process_activity_data(payload)
            else:
                raise ValueError(f"Unsupported content type: {payload['data']['content_type']}")
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _process_location_history(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process location history data"""
        processed_count = 0
        
        for record in payload['data']['records']:
            # Create GeoJSON point
            geom = {
                'type': 'Point',
                'coordinates': [record['longitude'], record['latitude']]
            }
            
            # Store in spatial database
            await self.spatial_store.insert_location(
                geom=geom,
                properties={
                    'user_id': payload['user_id'],
                    'timestamp': record['timestamp'],
                    'source': payload['data']['source']
                }
            )
            processed_count += 1
        
        return {
            'status': 'success',
            'processed': processed_count,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _process_activity_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process activity data"""
        # Store in time series database
        await self.timeseries_store.insert_metrics(
            metrics=payload['data'],
            timestamp=datetime.fromisoformat(payload['timestamp'])
        )
        
        return {
            'status': 'success',
            'processed': 1,
            'timestamp': datetime.utcnow().isoformat()
        } 