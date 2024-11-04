from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime, timezone
from models.stream import StreamEvent
from processors.validation.validators import EventValidator

class BaseEventProcessor(ABC):
    """Base class for all event processors"""
    
    def __init__(self):
        self.validator = EventValidator()
    
    async def process_pipeline(self, event: StreamEvent) -> Dict[str, Any]:
        """Main processing pipeline for all events"""
        try:
            # 1. Validation stage
            if not await self.validate(event):
                raise ValueError("Event validation failed")
            
            # 2. Normalization stage
            normalized_event = await self.normalize(event)
            
            # 3. Processing stage (implemented by specific processors)
            processed_result = await self.process(normalized_event)
            
            # 4. Post-processing stage
            return await self._post_process(processed_result)
            
        except Exception as e:
            # Error handling
            return {
                'error': str(e),
                'status': 'failed',
                'event_id': event.id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

    @abstractmethod
    async def process(self, event: StreamEvent) -> Dict[str, Any]:
        """Process an event and return the processed result"""
        pass

    async def validate(self, event: StreamEvent) -> bool:
        """Base validation for all events"""
        if not event:
            return False
            
        # Validate basic required fields
        required_fields = ['id', 'timestamp', 'stream_type', 'source', 'data']
        if not all(hasattr(event, field) for field in required_fields):
            return False
            
        # Validate timestamp
        if not self.validator.validate_timestamp(event.timestamp):
            return False
            
        # Validate data field requirements
        if not self.validator.validate_required_fields(event.data, ['event_type']):
            return False
            
        return True

    async def normalize(self, event: StreamEvent) -> StreamEvent:
        """Apply normalization pipeline to event"""
        # Timestamp standardization
        event.timestamp = self._standardize_timestamp(event.timestamp)
        
        # Text normalization
        if isinstance(event.data.get('text'), str):
            event.data['text'] = self._normalize_text(event.data['text'])
        
        # Location standardization
        if location := event.data.get('location'):
            event.data['location'] = self._standardize_location(location)
        
        # Add metadata
        event.metadata = event.metadata or {}
        event.metadata.update({
            'processed_at': datetime.now(timezone.utc).isoformat(),
            'source_identifier': f"{event.stream_type.value}_{event.source}",
            'processor_version': '1.0'
        })
        
        return event

    async def _post_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process results before returning"""
        result['processed_at'] = datetime.now(timezone.utc).isoformat()
        result['status'] = 'success'
        return result

    def _standardize_timestamp(self, timestamp: datetime) -> datetime:
        """Standardize timestamp to UTC ISO8601"""
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)

    def _normalize_text(self, text: str) -> str:
        """Normalize text content"""
        text = text.lower()
        text = text.strip()
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32)
        return text

    def _standardize_location(self, location: Dict) -> Dict:
        """Standardize location coordinates"""
        if 'lat' in location and 'lng' in location:
            location['lat'] = round(float(location['lat']), 6)
            location['lng'] = round(float(location['lng']), 6)
        return location