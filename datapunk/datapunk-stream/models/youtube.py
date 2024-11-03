from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class YouTubeEvent(BaseModel):
    video_id: str
    event_type: str
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] 