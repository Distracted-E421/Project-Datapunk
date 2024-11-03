from typing import Dict, Any
from models.stream import StreamEvent
from .base_processor import BaseEventProcessor
from core.config import get_settings
from datetime import datetime, timezone

class MapsProcessor(BaseEventProcessor):
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.event_types = {
            'location': self._process_location_event,
            'place_visit': self._process_place_visit_event,
            'route': self._process_route_event,
            'review': self._process_review_event,
            'preference': self._process_preference_event
        }

    async def process(self, event: StreamEvent) -> Dict[str, Any]:
        processor = self.event_types.get(event.data.get('event_type'))
        if not processor:
            raise ValueError(f"Unknown Maps event type: {event.data.get('event_type')}")
        return await processor(event)

    async def validate(self, event: StreamEvent) -> bool:
        """Validate Maps event data"""
        base_fields = ['id', 'timestamp', 'event_type']
        if not all(field in event.data for field in base_fields):
            return False
            
        # Validate based on event type
        event_type = event.data.get('event_type')
        if event_type == 'location':
            return all(field in event.data for field in ['latitude', 'longitude'])
        elif event_type == 'place_visit':
            return all(field in event.data for field in ['place_id', 'duration'])
        return True

    async def _process_location_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process location update events"""
        data = event.data
        return {
            'location': {
                'lat': data.get('latitude'),
                'lng': data.get('longitude'),
                'accuracy': data.get('accuracy'),
                'altitude': data.get('altitude'),
                'speed': data.get('speed'),
                'heading': data.get('heading')
            },
            'device': {
                'id': data.get('device_id'),
                'type': data.get('device_type')
            },
            'timestamp': event.timestamp.isoformat(),
            'activity': data.get('activity_type'),
            'battery_level': data.get('battery_level')
        }

    async def _process_place_visit_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process place visit events"""
        data = event.data
        return {
            'place': {
                'id': data.get('place_id'),
                'name': data.get('place_name'),
                'address': data.get('address'),
                'types': data.get('place_types', []),
                'location': {
                    'lat': data.get('latitude'),
                    'lng': data.get('longitude')
                }
            },
            'visit': {
                'arrival_time': data.get('arrival_time'),
                'departure_time': data.get('departure_time'),
                'duration_minutes': data.get('duration'),
                'confidence': data.get('confidence')
            },
            'timestamp': event.timestamp.isoformat()
        }

    async def _process_route_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process route/commute events"""
        data = event.data
        return {
            'route': {
                'origin': {
                    'place_id': data.get('origin_id'),
                    'name': data.get('origin_name'),
                    'location': {
                        'lat': data.get('origin_lat'),
                        'lng': data.get('origin_lng')
                    }
                },
                'destination': {
                    'place_id': data.get('destination_id'),
                    'name': data.get('destination_name'),
                    'location': {
                        'lat': data.get('destination_lat'),
                        'lng': data.get('destination_lng')
                    }
                },
                'mode': data.get('travel_mode'),
                'distance_meters': data.get('distance'),
                'duration_seconds': data.get('duration')
            },
            'timestamp': event.timestamp.isoformat()
        }
    
    async def _process_review_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process place review events"""
        data = event.data
        # Process review text through PII detection
        review_text = await self._handle_pii_content(data.get('review_text', ''))
        
        return {
            'review': {
                'place_id': data.get('place_id'),
                'rating': data.get('rating'),
                'text': review_text,
                'photos': data.get('photo_references', []),
                'timestamp': event.timestamp.isoformat(),
                'status': data.get('status', 'published')
            },
            'metadata': {
                'device_type': data.get('device_type'),
                'app_version': data.get('app_version'),
                'language': data.get('language')
            }
        }

    async def _process_preference_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process user preference events"""
        data = event.data
        return {
            'preferences': {
                'home_location': {
                    'place_id': data.get('home_place_id'),
                    'label': 'home'
                } if data.get('home_place_id') else None,
                'work_location': {
                    'place_id': data.get('work_place_id'),
                    'label': 'work'
                } if data.get('work_place_id') else None,
                'favorite_places': [
                    {
                        'place_id': place['id'],
                        'label': place['label']
                    } for place in data.get('favorite_places', [])
                ],
                'commute_preferences': {
                    'mode': data.get('preferred_mode'),
                    'avoid_highways': data.get('avoid_highways', False),
                    'avoid_tolls': data.get('avoid_tolls', False)
                }
            },
            'timestamp': event.timestamp.isoformat()
        }

    async def _handle_pii_content(self, text: str) -> str:
        """Handle PII detection and anonymization"""
        from api.middleware.pii import pii_detector
        return await pii_detector.anonymize_pii(text)