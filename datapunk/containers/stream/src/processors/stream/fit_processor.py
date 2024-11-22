from typing import Dict, Any
from models.stream import StreamEvent
from .base_processor import BaseEventProcessor
from core.config import get_settings
from datetime import datetime, timezone

class FitProcessor(BaseEventProcessor):
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.event_types = {
            'activity': self._process_activity_event,
            'daily_metrics': self._process_daily_metrics_event,
            'session': self._process_session_event,
            'sleep': self._process_sleep_event
        }

    async def process(self, event: StreamEvent) -> Dict[str, Any]:
        processor = self.event_types.get(event.data.get('event_type'))
        if not processor:
            raise ValueError(f"Unknown Fit event type: {event.data.get('event_type')}")
        return await processor(event)

    async def validate(self, event: StreamEvent) -> bool:
        """Validate Fit event data"""
        base_fields = ['id', 'timestamp', 'event_type']
        if not all(field in event.data for field in base_fields):
            return False
            
        event_type = event.data.get('event_type')
        if event_type == 'activity':
            return all(field in event.data for field in ['activity_type', 'duration'])
        elif event_type == 'daily_metrics':
            return all(field in event.data for field in ['date', 'metrics'])
        return True

    async def _process_activity_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process workout and activity events"""
        data = event.data
        return {
            'activity': {
                'type': data.get('activity_type'),
                'duration_ms': data.get('duration'),
                'distance_meters': data.get('distance'),
                'calories': data.get('calories_burned'),
                'steps': data.get('steps'),
                'heart_rate': {
                    'avg': data.get('avg_heart_rate'),
                    'max': data.get('max_heart_rate'),
                    'min': data.get('min_heart_rate')
                } if data.get('avg_heart_rate') else None
            },
            'device': {
                'type': data.get('device_type'),
                'model': data.get('device_model'),
                'manufacturer': data.get('manufacturer')
            },
            'timestamp': event.timestamp.isoformat(),
            'location': {
                'start': {
                    'lat': data.get('start_latitude'),
                    'lng': data.get('start_longitude')
                },
                'end': {
                    'lat': data.get('end_latitude'),
                    'lng': data.get('end_longitude')
                }
            } if data.get('start_latitude') else None
        }
        
    async def _process_daily_metrics_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process daily aggregated fitness metrics"""
        data = event.data
        return {
            'date': data.get('date'),
            'metrics': {
                'steps': data.get('steps_count'),
                'distance': {
                    'value': data.get('distance_meters'),
                    'unit': 'meters'
                },
                'calories': {
                    'active': data.get('active_calories'),
                    'bmr': data.get('bmr_calories')
                },
                'heart_rate': {
                    'avg': data.get('avg_heart_rate'),
                    'min': data.get('min_heart_rate'),
                    'max': data.get('max_heart_rate')
                } if data.get('avg_heart_rate') else None,
                'active_minutes': data.get('active_minutes')
            },
            'sources': data.get('data_sources', []),
            'timestamp': event.timestamp.isoformat()
        }

    async def _process_sleep_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process sleep tracking data"""
        data = event.data
        return {
            'sleep': {
                'start_time': data.get('sleep_start_time'),
                'end_time': data.get('sleep_end_time'),
                'duration_minutes': data.get('sleep_duration_minutes'),
                'quality': data.get('sleep_quality'),
                'stages': {
                    'deep': data.get('deep_sleep_minutes'),
                    'light': data.get('light_sleep_minutes'),
                    'rem': data.get('rem_sleep_minutes'),
                    'awake': data.get('awake_minutes')
                } if data.get('deep_sleep_minutes') is not None else None
            },
            'device': {
                'type': data.get('device_type'),
                'model': data.get('device_model')
            },
            'timestamp': event.timestamp.isoformat()
        }

    async def _process_session_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process fitness session data"""
        data = event.data
        return {
            'session': {
                'id': data.get('session_id'),
                'name': data.get('session_name'),
                'description': data.get('description'),
                'activity_type': data.get('activity_type'),
                'start_time': data.get('start_time'),
                'end_time': data.get('end_time'),
                'duration_ms': data.get('duration')
            },
            'metrics': {
                'distance': data.get('distance_meters'),
                'calories': data.get('calories_burned'),
                'steps': data.get('steps_count'),
                'heart_rate_zones': data.get('heart_rate_zones')
            },
            'segments': data.get('segments', []),
            'timestamp': event.timestamp.isoformat()
        }