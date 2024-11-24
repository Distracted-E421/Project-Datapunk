"""Type definitions for policy enforcement.

This module defines the core types and data structures used in the policy enforcement system.
It provides a flexible framework for implementing and managing security policies with different
enforcement levels and actions.

Key components:
- EnforcementLevel: Defines how strictly policies should be enforced
- EnforcementAction: Specifies actions to take when policies are violated
- EnforcementContext: Captures the full context of a request for policy evaluation
- EnforcementResult: Records the outcome of policy enforcement
"""

from typing import Dict, List, Optional, Set, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, time

class EnforcementLevel(Enum):
    """Policy enforcement levels defining the strictness of policy application.
    
    These levels allow for flexible policy enforcement based on different security needs:
    - STRICT: Zero-tolerance enforcement for high-security contexts
    - STANDARD: Regular enforcement for normal operations
    - PERMISSIVE: Relaxed enforcement for testing or special cases
    - AUDIT: Monitoring mode without active enforcement
    """
    STRICT = "strict"       # No exceptions allowed
    STANDARD = "standard"   # Normal enforcement
    PERMISSIVE = "permissive"  # Allow some exceptions
    AUDIT = "audit"        # Log only, no enforcement

class EnforcementAction(Enum):
    """Actions that can be taken when a policy violation is detected.
    
    These actions represent the graduated response system:
    - BLOCK: Immediately prevent the action (highest severity)
    - WARN: Allow but issue warning (medium severity)
    - LOG: Silent logging (low severity)
    - NOTIFY: Alert administrators (special handling)
    """
    BLOCK = "block"        # Block the request
    WARN = "warn"         # Allow but warn
    LOG = "log"          # Log only
    NOTIFY = "notify"    # Notify admins

@dataclass
class EnforcementContext:
    """Context object capturing all relevant information for policy evaluation.
    
    This class serves as a comprehensive snapshot of the request context,
    ensuring all necessary information is available for policy decisions.
    
    Note: The metadata field can be used for extending context without
    modifying the class structure.
    """
    request_id: str        # Unique identifier for request tracing
    timestamp: datetime    # When the request was received
    client_ip: str        # Source IP for geolocation/rate limiting
    user_agent: str       # Client software identification
    resource_path: str    # Target resource being accessed
    http_method: str      # HTTP verb (GET, POST, etc.)
    headers: Dict[str, str]  # Request headers for additional context
    query_params: Dict[str, str]  # URL parameters
    metadata: Optional[Dict[str, Any]] = None  # Extensible metadata

@dataclass
class EnforcementResult:
    """Records the outcome of policy enforcement evaluation.
    
    This class provides a complete audit trail of the policy decision,
    including which rules were evaluated and why the decision was made.
    
    Important: The context field should include any relevant details that
    influenced the decision for audit purposes.
    """
    allowed: bool         # Final decision on request
    action: EnforcementAction  # Action taken
    rules_evaluated: List[str]  # All rules considered
    rules_failed: List[str]    # Rules that triggered violations
    context: Dict[str, Any]    # Decision context for auditing
    timestamp: datetime        # When decision was made 