from typing import Dict, Any, Optional
from datetime import datetime, timezone
from models.stream import StreamEvent
from .base_processor import BaseEventProcessor

class GoogleEventProcessor(BaseEventProcessor):
    def __init__(self):
        self.processors = {
            'maps': self._process_maps_event,
            'youtube': self._process_youtube_event,
            'fit': self._process_fit_event,
            'photos': self._process_photos_event,
            'play': self._process_play_event
        }

    async def process(self, event: StreamEvent) -> Dict[str, Any]:
        """Process Google-specific events"""
        try:
            # Get specific processor based on source
            processor = self.processors.get(event.source)
            if not processor:
                raise ValueError(f"Unknown Google event source: {event.source}")
            
            # Validate event
            if not await self.validate(event):
                raise ValueError("Event validation failed")
            
            # Normalize event
            normalized_event = await self.normalize(event)
            
            # Process with specific handler
            result = await processor(normalized_event)
            
            # Add processing metadata
            result['processed_at'] = datetime.now(timezone.utc).isoformat()
            result['processor_version'] = '1.0'
            
            return result
            
        except Exception as e:
            # Log error and return failure result
            return {
                'error': str(e),
                'status': 'failed',
                'event_id': event.id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    async def validate(self, event: StreamEvent) -> bool:
        """Validate Google event data"""
        required_fields = ['id', 'timestamp', 'source', 'data']
        return all(hasattr(event, field) for field in required_fields)

    async def _process_maps_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process Maps-specific events"""
        data = event.data
        processed_data = {
            'location': {
                'lat': data.get('latitude'),
                'lng': data.get('longitude'),
                'accuracy': data.get('accuracy'),
            },
            'place': {
                'id': data.get('place_id'),
                'name': data.get('place_name'),
                'address': data.get('address'),
            },
            'timestamp': event.timestamp,
            'event_type': data.get('event_type'),  # visit, departure, review
            'duration': data.get('duration'),
        }
        return processed_data

    async def _process_youtube_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process YouTube-specific events"""
        data = event.data
        processed_data = {
            'video_id': data.get('video_id'),
            'channel_id': data.get('channel_id'),
            'action_type': data.get('action'),  # watch, like, comment
            'duration': data.get('watch_duration'),
            'timestamp': event.timestamp,
            'metadata': {
                'title': data.get('video_title'),
                'channel_name': data.get('channel_name'),
            }
        }
        return processed_data