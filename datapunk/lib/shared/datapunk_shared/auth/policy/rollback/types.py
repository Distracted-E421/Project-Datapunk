"""Type definitions for policy rollbacks."""
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class RollbackStatus(Enum):
    """Status of rollback operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RollbackRisk(Enum):
    """Risk levels for rollback operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class RollbackContext:
    """Context for rollback operations."""
    rollback_id: str
    policy_id: str
    initiator_id: str
    timestamp: datetime
    reason: str
    affected_services: List[str]
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class RollbackResult:
    """Result of rollback operation."""
    success: bool
    status: RollbackStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    affected_resources: List[str] = None
    metrics: Optional[Dict[str, Any]] = None 