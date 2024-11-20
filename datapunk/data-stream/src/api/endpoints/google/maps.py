from fastapi import APIRouter, Depends, Security, HTTPException
from typing import Dict, Any
from models.stream import StreamEvent
from processors.stream.maps_processor import MapsProcessor
from api.middleware.auth import verify_token
from api.middleware.rate_limit import rate_limiter

router = APIRouter(prefix="/maps", tags=["maps"])
processor = MapsProcessor()

@router.post("/events", response_model=Dict[str, Any])
async def process_maps_event(
    event: StreamEvent,
    token_data = Security(verify_token, scopes=["google"])
):
    """Process Maps events with rate limiting and authentication"""
    await rate_limiter.check_rate_limit()
    return await processor.process(event)

@router.get("/preferences", response_model=Dict[str, Any])
async def get_maps_preferences(
    token_data = Security(verify_token, scopes=["google"])
):
    """Get user's Maps preferences"""
    await rate_limiter.check_rate_limit()
    # Implementation for retrieving user preferences
    pass