# datapunk/containers/nexus/src/routes/upload.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from core.auth import validate_token
from core.validation import validate_request
from services.lake import LakeService
from services.stream import StreamService

router = APIRouter()

@router.post("/upload/google-takeout", tags=["upload"])
async def upload_google_takeout(
    file: UploadFile = File(...),
    token: str = Depends(validate_token)
):
    """Gateway endpoint for Google Takeout uploads"""
    try:
        # Validate request through Gateway validation
        await validate_request(file, "google_takeout")
        
        # Route to Lake Service for processing
        lake_service = LakeService()
        result = await lake_service.process_takeout(file)
        
        # Stream events to Stream Service
        stream_service = StreamService()
        await stream_service.publish_events("google_takeout", result)
        
        return result
        
    except Exception as e:
        # Log error through observability stack
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))