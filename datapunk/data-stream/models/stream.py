from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

class StreamType(Enum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    ENTERTAINMENT = "entertainment"
    GENERIC = "generic"

class StreamStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    CLOSED = "closed"

class StreamConfig(BaseModel):
    batch_size: int = Field(default=100, gt=0)
    buffer_timeout: float = Field(default=1.0, gt=0)
    max_retries: int = Field(default=3, ge=0)
    backoff_factor: float = Field(default=1.5, gt=0)

class StreamEvent(BaseModel):
    id: str
    stream_type: StreamType
    timestamp: datetime
    source: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class StreamState(BaseModel):
    stream_id: str
    status: StreamStatus
    last_processed: Optional[datetime] = None
    error_count: int = 0
    current_position: Optional[str] = None
    config: StreamConfig
    events_processed: int = 0
    events_failed: int = 0