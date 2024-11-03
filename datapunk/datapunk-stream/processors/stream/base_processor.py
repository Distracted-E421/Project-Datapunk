from typing import Dict, Any, Optional
from models.stream import StreamEvent
from abc import ABC, abstractmethod

class BaseEventProcessor(ABC):
    """Base class for all event processors"""
    
    @abstractmethod
    async def process(self, event: StreamEvent) -> Dict[str, Any]:
        """Process an event and return the processed result"""
        pass
    
    @abstractmethod
    async def validate(self, event: StreamEvent) -> bool:
        """Validate event data"""
        pass
    
    async def normalize(self, event: StreamEvent) -> StreamEvent:
        """Apply normalization pipeline to event"""
        # Reference normalization pipeline config from datapunk-stream.md lines 97-111
        return event