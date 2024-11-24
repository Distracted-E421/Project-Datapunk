"""Type definitions for policy enforcement."""
from typing import Dict, List, Optional, Set, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, time

class EnforcementLevel(Enum):
    """Policy enforcement levels."""
    STRICT = "strict"       # No exceptions allowed
    STANDARD = "standard"   # Normal enforcement
    PERMISSIVE = "permissive"  # Allow some exceptions
    AUDIT = "audit"        # Log only, no enforcement

class EnforcementAction(Enum):
    """Actions taken on policy violations."""
    BLOCK = "block"        # Block the request
    WARN = "warn"         # Allow but warn
    LOG = "log"          # Log only
    NOTIFY = "notify"    # Notify admins

@dataclass
class EnforcementContext:
    """Context for policy enforcement."""
    request_id: str
    timestamp: datetime
    client_ip: str
    user_agent: str
    resource_path: str
    http_method: str
    headers: Dict[str, str]
    query_params: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class EnforcementResult:
    """Result of policy enforcement."""
    allowed: bool
    action: EnforcementAction
    rules_evaluated: List[str]
    rules_failed: List[str]
    context: Dict[str, Any]
    timestamp: datetime 