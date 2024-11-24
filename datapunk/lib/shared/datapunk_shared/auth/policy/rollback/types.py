"""Type definitions for policy rollbacks.

This module defines the core data structures and enums used in the policy rollback system,
which handles the reverting of security policy changes in a controlled manner.

Key components:
- RollbackStatus: Tracks the lifecycle states of rollback operations
- RollbackRisk: Assesses potential impact of rollback operations
- RollbackContext: Captures metadata and context for rollback requests
- RollbackResult: Records outcomes and metrics of rollback operations
"""
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class RollbackStatus(Enum):
    """Status of rollback operations.
    
    Represents the complete lifecycle of a rollback operation:
    - PENDING: Initial state, rollback scheduled but not started
    - IN_PROGRESS: Actively executing rollback steps
    - COMPLETED: Successfully finished all rollback operations
    - FAILED: Encountered error during rollback process
    - CANCELLED: Manually stopped before completion
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RollbackRisk(Enum):
    """Risk levels for rollback operations.
    
    Categorizes potential impact of rollback operations:
    - LOW: Minimal impact, unlikely to affect system stability
    - MEDIUM: Moderate impact, may affect non-critical services
    - HIGH: Significant impact, affects critical services but recoverable
    - CRITICAL: Severe impact, potential system-wide disruption
    
    Used for approval workflows and determining rollback strategy.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class RollbackContext:
    """Context for rollback operations.
    
    Captures all necessary information to execute and audit a rollback:
    
    Attributes:
        rollback_id: Unique identifier for the rollback operation
        policy_id: ID of the policy being rolled back
        initiator_id: ID of user/system initiating the rollback
        timestamp: When the rollback was requested
        reason: Justification for the rollback
        affected_services: List of services impacted by rollback
        metadata: Optional additional context (e.g., approval chain, related tickets)
    """
    rollback_id: str
    policy_id: str
    initiator_id: str
    timestamp: datetime
    reason: str
    affected_services: List[str]
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class RollbackResult:
    """Result of rollback operation.
    
    Records the outcome and performance metrics of a rollback operation:
    
    Attributes:
        success: Whether the rollback completed successfully
        status: Final status of the rollback operation
        start_time: When rollback execution began
        end_time: When rollback completed/failed (None if still running)
        error_message: Details of failure if unsuccessful
        affected_resources: List of resources modified during rollback
        metrics: Optional performance/impact metrics (e.g., duration, resource usage)
    
    NOTE: affected_resources should be initialized as an empty list rather than None
    TODO: Add validation to ensure end_time >= start_time when present
    """
    success: bool
    status: RollbackStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    affected_resources: List[str] = None  # FIXME: Initialize as empty list
    metrics: Optional[Dict[str, Any]] = None 