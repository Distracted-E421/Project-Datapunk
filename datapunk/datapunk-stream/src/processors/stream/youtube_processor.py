from typing import Dict, Any
from models.stream import StreamEvent
from .base_processor import BaseEventProcessor
from core.config import get_settings

class YouTubeProcessor(BaseEventProcessor):
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.event_types = {
            'watch': self._process_watch_event,
            'like': self._process_like_event,
            'comment': self._process_comment_event,
            'playlist': self._process_playlist_event
        }

    async def process(self, event: StreamEvent) -> Dict[str, Any]:
        processor = self.event_types.get(event.data.get('event_type'))
        if not processor:
            raise ValueError(f"Unknown YouTube event type: {event.data.get('event_type')}")
        return await processor(event)

    async def _process_watch_event(self, event: StreamEvent) -> Dict[str, Any]:
        return {
            'video_id': event.data.get('video_id'),
            'duration': event.data.get('watch_duration'),
            'timestamp': event.timestamp,
            'player_state': event.data.get('player_state'),
            'quality': event.data.get('playback_quality'),
            'metadata': {
                'title': event.data.get('video_title'),
                'channel': event.data.get('channel_name')
            }
        } 