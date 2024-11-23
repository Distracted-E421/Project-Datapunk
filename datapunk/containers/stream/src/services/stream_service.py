# datapunk/containers/stream/src/services/stream_service.py

from typing import Dict, Any
from datetime import datetime
from core.messaging import MessageQueue
from core.cache import StreamCache

class StreamService:
    def __init__(self):
        self.message_queue = MessageQueue()
        self.cache = StreamCache()
        
    async def publish_events(self, source: str, data: Dict[str, Any]):
        """Publish events to Stream Service"""
        try:
            # Create stream events
            events = self._create_events(source, data)
            
            # Cache stream state
            await self.cache.set_stream_state(source, {
                "last_event": datetime.utcnow().isoformat(),
                "event_count": len(events)
            })
            
            # Publish to message queue
            await self.message_queue.publish_batch("events", events)
            
        except Exception as e:
            logger.error(f"Stream publishing failed: {str(e)}")
            raise