import json
from typing import Dict, Any
from models.stream import StreamEvent
from .base_processor import BaseEventProcessor
from core.config import get_settings
from datetime import datetime, timezone

class PhotosProcessor(BaseEventProcessor):
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.event_types = {
            'upload': self._process_upload_event,
            'album': self._process_album_event,
            'sharing': self._process_sharing_event,
            'metadata': self._process_metadata_event
        }

    async def process(self, event: StreamEvent) -> Dict[str, Any]:
        processor = self.event_types.get(event.data.get('event_type'))
        if not processor:
            raise ValueError(f"Unknown Photos event type: {event.data.get('event_type')}")
        return await processor(event)

    async def validate(self, event: StreamEvent) -> bool:
        """Validate Photos event data"""
        base_fields = ['id', 'timestamp', 'event_type']
        if not all(field in event.data for field in base_fields):
            return False
            
        event_type = event.data.get('event_type')
        if event_type == 'upload':
            return all(field in event.data for field in ['photo_id', 'mime_type'])
        elif event_type == 'album':
            return all(field in event.data for field in ['album_id', 'title'])
        return True

    async def _process_upload_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process photo/video upload events"""
        data = event.data
        return {
            'media': {
                'id': data.get('photo_id'),
                'type': data.get('mime_type'),
                'filename': data.get('filename'),
                'size_bytes': data.get('size'),
                'width': data.get('width'),
                'height': data.get('height'),
                'camera': {
                    'make': data.get('camera_make'),
                    'model': data.get('camera_model'),
                    'iso': data.get('iso'),
                    'focal_length': data.get('focal_length'),
                    'exposure_time': data.get('exposure_time')
                } if data.get('camera_make') else None
            },
            'location': {
                'lat': data.get('latitude'),
                'lng': data.get('longitude')
            } if data.get('latitude') else None,
            'timestamp': event.timestamp.isoformat(),
            'upload_source': data.get('upload_source')
        }
        
    async def _process_album_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process album-related events"""
        data = event.data
        return {
            'album': {
                'id': data.get('album_id'),
                'title': data.get('title'),
                'description': data.get('description'),
                'item_count': data.get('item_count'),
                'cover_photo_id': data.get('cover_photo_id'),
                'media_type': data.get('media_types', []),
                'is_writeable': data.get('is_writeable', True)
            },
            'sharing': {
                'share_token': data.get('share_token'),
                'is_shared': data.get('is_shared', False),
                'share_info': await self._handle_pii_content(
                json.dumps(data.get('share_info', {}))
                )
            } if data.get('is_shared') else None,
            'timestamp': event.timestamp.isoformat()
        }

    async def _process_sharing_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process sharing-related events"""
        data = event.data
        return {
            'sharing': {
                'resource_id': data.get('resource_id'),  # album_id or photo_id
                'resource_type': data.get('resource_type'),  # album or photo
                'share_token': data.get('share_token'),
                'action': data.get('action'),  # created, modified, removed
                'shared_with': await self._handle_pii_content(
                    json.dumps(data.get('shared_with', []))
                ),
                'permissions': data.get('permissions', [])
            },
            'timestamp': event.timestamp.isoformat()
        }

    async def _process_metadata_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process metadata update events"""
        data = event.data
        return {
            'metadata': {
                'photo_id': data.get('photo_id'),
                'description': data.get('description'),
                'location': {
                    'lat': data.get('latitude'),
                    'lng': data.get('longitude'),
                    'place_name': data.get('place_name')
                } if data.get('latitude') else None,
                'people': data.get('people_tags', []),
                'labels': data.get('labels', []),
                'date_taken': data.get('date_taken'),
                'camera_info': {
                    'make': data.get('camera_make'),
                    'model': data.get('camera_model'),
                    'settings': data.get('camera_settings', {})
                } if data.get('camera_make') else None
            },
            'timestamp': event.timestamp.isoformat()
        }