from typing import Dict, List, Optional, Union, Set, Any
from datetime import datetime, time
from enum import Enum
from dataclasses import dataclass

# Core security policy type definitions aligned with NIST SP 800-53
# These types correspond to common security control families
class PolicyType(Enum):
    """Types of security policies."""
    ACCESS = "access"         # Identity and access management controls
    AUTHENTICATION = "auth"   # User authentication mechanisms and requirements
    ENCRYPTION = "encrypt"    # Data protection and cryptographic controls
    AUDIT = "audit"          # Security logging and monitoring requirements
    COMPLIANCE = "comply"     # Regulatory and standards compliance rules
    ROTATION = "rotate"      # Credential and key lifecycle management
    RATE_LIMIT = "rate"      # Request rate and resource usage controls

class PolicyStatus(Enum):
    """
    Lifecycle states for security policies.
    Follows a standard workflow: DRAFT -> PENDING -> ACTIVE -> (DISABLED/ARCHIVED)
    """
    DRAFT = "draft"          # Initial creation/modification state
    ACTIVE = "active"        # Production enforcement state
    DISABLED = "disabled"    # Temporarily suspended but retaining config
    ARCHIVED = "archived"    # Permanently deactivated for historical reference
    PENDING = "pending"      # Under review/approval process

class RiskLevel(Enum):
    """
    Risk classification levels for policy changes.
    Used in change management and approval workflows.
    Aligned with standard risk management frameworks.
    """
    LOW = "low"          # Minimal impact, routine changes
    MEDIUM = "medium"    # Moderate impact, requires review
    HIGH = "high"        # Significant impact, requires approval
    CRITICAL = "critical"  # Maximum impact, requires executive approval

@dataclass
class TimeWindow:
    """
    Defines temporal bounds for policy enforcement.
    Used for scheduling policy activation periods and maintenance windows.
    """
    start_time: time     # Daily start time for policy enforcement
    end_time: time      # Daily end time for policy enforcement
    days: Set[int]      # Days of week (0=Monday, 6=Sunday) for enforcement
    timezone: str = "UTC"  # Reference timezone for time calculations

@dataclass
class PolicyRule:
    """
    Atomic policy enforcement unit containing conditions and resulting actions.
    Forms the building blocks of complex policy definitions.
    """
    rule_id: str        # Unique identifier for the rule
    rule_type: str      # Classification of rule behavior
    conditions: Dict[str, Any]  # Criteria that trigger rule evaluation
    actions: List[str]  # Actions to take when conditions are met
    priority: int = 0   # Execution priority (higher = evaluated first)
    metadata: Optional[Dict[str, Any]] = None  # Additional rule context/tags

@dataclass
class Policy:
    """
    Complete security policy definition combining rules and metadata.
    Represents a versioned, time-bound security control implementation.
    """
    policy_id: str      # Unique policy identifier
    type: PolicyType    # Security control category
    status: PolicyStatus  # Current lifecycle state
    rules: List[PolicyRule]  # Ordered list of enforcement rules
    version: str        # Semantic version of policy
    created_at: datetime  # Creation timestamp
    created_by: str     # Identity of policy author
    effective_from: datetime  # Policy activation timestamp
    effective_until: Optional[datetime] = None  # Optional expiration
    description: Optional[str] = None  # Human-readable policy summary
    metadata: Optional[Dict[str, Any]] = None  # Additional policy context

@dataclass
class PolicyValidationResult:
    """
    Validation outcome for policy changes.
    Used in policy review and approval workflows.
    """
    valid: bool         # Overall validation status
    issues: List[str]   # Critical problems blocking implementation
    warnings: List[str]  # Non-blocking concerns requiring attention
    risk_level: RiskLevel  # Assessed impact level of changes
    breaking_changes: List[str]  # Backwards compatibility impacts
    metadata: Optional[Dict[str, Any]] = None  # Validation context

@dataclass
class PolicyEvaluationResult:
    """
    Runtime evaluation result for policy enforcement.
    Captures decision outcome and supporting context.
    """
    allowed: bool       # Final authorization decision
    matched_rules: List[str]  # Rules that influenced decision
    reason: Optional[str] = None  # Human-readable explanation
    context: Optional[Dict[str, Any]] = None  # Evaluation parameters
    metadata: Optional[Dict[str, Any]] = None  # Additional decision context
  