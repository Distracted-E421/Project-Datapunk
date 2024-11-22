om fastapi import APIRouter, Security, HTTPException, Query, Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from models.stream import StreamEvent
from processors.stream.instagram_processor import InstagramProcessor
from api.middleware.auth import verify_token
from api.middleware.rate_limit import rate_limiter

router = APIRouter(prefix="/instagram", tags=["instagram"])
processor = InstagramProcessor()

@router.post("/events", response_model=Dict[str, Any])
async def process_instagram_event(
    event: StreamEvent,
    token_data = Security(verify_token, scopes=["meta"])
):
    """Process Instagram events with rate limiting"""
    await rate_limiter.check_rate_limit()
    return await processor.process(event)

@router.get("/insights", response_model=Dict[str, Any])
async def get_instagram_insights(
    metric_types: List[str] = Query(...),
    period: str = Query(default="day"),
    token_data = Security(verify_token, scopes=["meta"])
):
    """Get Instagram insights with rate limiting"""
    await rate_limiter.check_rate_limit()
    # Implementation for retrieving insights
    pass

@router.get("/media/{media_id}", response_model=Dict[str, Any])
async def get_media_details(
    media_id: str = Path(..., title="The ID of the media item"),
    token_data = Security(verify_token, scopes=["meta"])
):
    """Get details for a specific media item"""
    await rate_limiter.check_rate_limit()
    # Implementation for retrieving media details
    pass

@router.get("/insights/account", response_model=Dict[str, Any])
async def get_account_insights(
    period: str = Query(default="day", enum=["day", "week", "month"]),
    metrics: List[str] = Query(default=["impressions", "reach", "profile_views"]),
    token_data = Security(verify_token, scopes=["meta"])
):
    """Get account-level insights"""
    await rate_limiter.check_rate_limit()
    # Implementation for account insights
    pass