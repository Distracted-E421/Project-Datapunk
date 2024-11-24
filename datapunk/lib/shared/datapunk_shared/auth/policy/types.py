from typing import Dict, List, Optional, Union, Set, Any
from datetime import datetime, time
from enum import Enum
from dataclasses import dataclass

class PolicyType(Enum):
    """Types of security policies."""
    ACCESS = "access"         # Access control
    AUTHENTICATION = "auth"   # Authentication
    ENCRYPTION = "encrypt"    # Encryption
    AUDIT = "audit"          # Audit logging
    COMPLIANCE = "comply"     # Compliance
    ROTATION = "rotate"      # Key rotation
    RATE_LIMIT = "rate"      # Rate limiting

class PolicyStatus(Enum):
    """Status of policy."""
    DRAFT = "draft"          # Not yet active
    ACTIVE = "active"        # Currently enforced
    DISABLED = "disabled"    # Temporarily disabled
    ARCHIVED = "archived"    # No longer used
    PENDING = "pending"      # Awaiting approval

class RiskLevel(Enum):
    """Risk levels for policy changes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TimeWindow:
    """Time window for policy enforcement."""
    start_time: time
    end_time: time
    days: Set[int]  # 0=Monday, 6=Sunday
    timezone: str = "UTC"

@dataclass
class PolicyRule:
    """Individual policy rule."""
    rule_id: str
    rule_type: str
    conditions: Dict[str, Any]
    actions: List[str]
    priority: int = 0
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Policy:
    """Security policy definition."""
    policy_id: str
    type: PolicyType
    status: PolicyStatus
    rules: List[PolicyRule]
    version: str
    created_at: datetime
    created_by: str
    effective_from: datetime
    effective_until: Optional[datetime] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class PolicyValidationResult:
    """Result of policy validation."""
    valid: bool
    issues: List[str]
    warnings: List[str]
    risk_level: RiskLevel
    breaking_changes: List[str]
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class PolicyEvaluationResult:
    """Result of policy evaluation."""
    allowed: bool
    matched_rules: List[str]
    reason: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None 