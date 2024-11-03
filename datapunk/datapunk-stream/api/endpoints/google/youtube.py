from fastapi import APIRouter, Depends, Security
from typing import Dict, Any
from models.stream import StreamEvent
from processors.stream.youtube_processor import YouTubeProcessor
from api.middleware.auth import verify_token
from api.middleware.rate_limit import rate_limiter

router = APIRouter(prefix="/youtube", tags=["youtube"])
processor = YouTubeProcessor()

@router.post("/events", response_model=Dict[str, Any])
async def process_youtube_event(
    event: StreamEvent,
    token_data = Security(verify_token, scopes=["google"])
):
    await rate_limiter.check_rate_limit()
    return await processor.process(event) 