from typing import Dict, Any
from models.stream import StreamEvent
from .base_processor import BaseEventProcessor
from core.config import get_settings
from datetime import datetime, timezone

class InstagramProcessor(BaseEventProcessor):
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.event_types = {
            'post': self._process_post_event,
            'story': self._process_story_event,
            'reel': self._process_reel_event,
            'comment': self._process_comment_event,
            'direct': self._process_direct_event
        }

    async def process(self, event: StreamEvent) -> Dict[str, Any]:
        processor = self.event_types.get(event.data.get('event_type'))
        if not processor:
            raise ValueError(f"Unknown Instagram event type: {event.data.get('event_type')}")
        return await processor(event)

    async def _process_post_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process Instagram post events"""
        data = event.data
        # Process caption through PII detection
        caption = await self._handle_pii_content(data.get('caption', ''))
        
        return {
            'post': {
                'id': data.get('post_id'),
                'type': data.get('media_type'),  # image, video, carousel
                'caption': caption,
                'location': {
                    'id': data.get('location_id'),
                    'name': data.get('location_name'),
                    'lat': data.get('latitude'),
                    'lng': data.get('longitude')
                } if data.get('location_id') else None,
                'media': [
                    {
                        'id': media.get('id'),
                        'url': media.get('url'),
                        'type': media.get('type')
                    } for media in data.get('media', [])
                ]
            },
            'engagement': {
                'likes': data.get('like_count', 0),
                'comments': data.get('comment_count', 0),
                'saves': data.get('save_count', 0),
                'shares': data.get('share_count', 0)
            },
            'timestamp': event.timestamp.isoformat()
        }

    async def _handle_pii_content(self, text: str) -> str:
        """Handle PII detection and anonymization"""
        from api.middleware.pii import pii_detector
        return await pii_detector.anonymize_pii(text)
    
    async def _process_story_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process Instagram story events"""
        data = event.data
        caption = await self._handle_pii_content(data.get('caption', ''))
        
        return {
            'story': {
                'id': data.get('story_id'),
                'type': data.get('media_type'),
                'caption': caption,
                'media_url': data.get('media_url'),
                'duration': data.get('duration'),
                'mentions': await self._handle_pii_content(
                    json.dumps(data.get('mentions', []))
                ),
                'stickers': data.get('stickers', []),
                'is_highlight': data.get('is_highlight', False)
            },
            'engagement': {
                'views': data.get('view_count', 0),
                'replies': data.get('reply_count', 0)
            },
            'timestamp': event.timestamp.isoformat(),
            'expiration': data.get('expiration_timestamp')
        }

    async def _process_reel_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process Instagram reel events"""
        data = event.data
        caption = await self._handle_pii_content(data.get('caption', ''))
        
        return {
            'reel': {
                'id': data.get('reel_id'),
                'caption': caption,
                'media_url': data.get('media_url'),
                'duration': data.get('duration'),
                'audio_track': {
                    'id': data.get('audio_id'),
                    'title': data.get('audio_title'),
                    'artist': data.get('audio_artist')
                } if data.get('audio_id') else None,
                'effects': data.get('effects', [])
            },
            'engagement': {
                'plays': data.get('play_count', 0),
                'likes': data.get('like_count', 0),
                'comments': data.get('comment_count', 0),
                'shares': data.get('share_count', 0)
            },
            'timestamp': event.timestamp.isoformat()
        }

    async def _process_comment_event(self, event: StreamEvent) -> Dict[str, Any]:
        """Process Instagram comment events"""
        data = event.data
        comment_text = await self._handle_pii_content(data.get('text', ''))
        
        return {
            'comment': {
                'id': data.get('comment_id'),
                'parent_id': data.get('parent_id'),  # For replies
                'text': comment_text,
                'post_id': data.get('post_id'),
                'is_reply': data.get('is_reply', False)
            },
            'engagement': {
                'likes': data.get('like_count', 0),
                'replies': data.get('reply_count', 0)
            },
            'timestamp': event.timestamp.isoformat()
        }