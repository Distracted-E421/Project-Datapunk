"""
API key policy management and validation.

This module implements a comprehensive policy framework for API key management with:
- Granular access control through different key types and permissions
- Configurable security controls including TLS, IP whitelisting, and encryption
- Resource quotas and rate limiting for usage control
- Compliance enforcement with audit trails and data classification
- Time-based access restrictions and circuit breaker patterns

Key Components:
- KeyType: Enumeration of API key access levels
- KeyPolicy: Core policy definition combining all security and access controls
- Pre-defined templates: ANALYTICS_POLICY, EMERGENCY_POLICY, TEMPORARY_POLICY

Implementation Notes:
- All time windows use UTC by default to avoid timezone ambiguity
- Circuit breaker pattern helps prevent cascade failures
- Resource restrictions support both allowlist and denylist patterns
"""

from typing import Dict, Set, Optional, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass
from datetime import time

from ..core.types import ResourceType
from ..types import Metadata

if TYPE_CHECKING:
    from ....monitoring import MetricsClient

class KeyType(Enum):
    """
    Hierarchical API key access levels from most to least privileged.
    
    ADMIN: Reserved for system administrators with full access
    SERVICE: For authenticated service-to-service communication
    READ_ONLY: Data access without modification rights
    LIMITED: Restricted to specific API endpoints or resources
    ANALYTICS: Specialized for data analysis and reporting
    TEMPORARY: Time-bound access for contractors or temporary needs
    EMERGENCY: Break-glass access with enhanced monitoring
    GEO_RESTRICTED: Region-specific access for compliance
    """

@dataclass
class ComplianceRequirements:
    """
    Compliance controls for regulatory and security standards.
    
    audit_level options:
    - minimal: Basic request logging
    - standard: Detailed access logs with resource tracking
    - full: Complete audit trail with data access monitoring
    
    data_classification aligns with standard security levels:
    - public: Freely accessible data
    - internal: Organization-wide access
    - confidential: Limited to specific roles
    - restricted: Highest sensitivity requiring special handling
    """
    encryption_required: bool = False
    audit_level: str = "standard"  # minimal, standard, full
    require_mfa: bool = False
    data_classification: str = "public"  # public, internal, confidential, restricted
    geo_restrictions: Optional[Set[str]] = None  # ISO country codes

@dataclass
class SecurityControls:
    """
    Technical security measures for API access.
    
    NOTE: require_https should only be disabled for internal dev environments
    TODO: Add support for JWT-based authentication
    FIXME: IP whitelist validation needs improvement for CIDR ranges
    """
    require_https: bool = True
    allowed_cipher_suites: Optional[Set[str]] = None
    min_tls_version: str = "1.2"
    require_client_certs: bool = False
    ip_whitelist: Optional[Set[str]] = None
    allowed_domains: Optional[Set[str]] = None

@dataclass
class ResourceQuota:
    """
    Usage limits for resource consumption.
    
    All quotas are enforced on a per-key basis and reset daily.
    Set any quota to None for unlimited access (use with caution).
    """
    daily_requests: int = 10000
    concurrent_requests: int = 10
    storage_mb: Optional[int] = None
    compute_minutes: Optional[int] = None
    bandwidth_mb: Optional[int] = None

@dataclass
class TimeWindow:
    """
    Schedule-based access control.
    
    days uses ISO weekday numbers (0=Monday, 6=Sunday) for clarity
    and international compatibility. All times are handled in the
    specified timezone (UTC default) to avoid DST complications.
    """
    start_time: time
    end_time: time
    days: Set[int]  # 0=Monday, 6=Sunday
    timezone: str = "UTC"

@dataclass
class CircuitBreaker:
    """
    Fault tolerance configuration to prevent cascade failures.
    
    Implements standard circuit breaker pattern with three states:
    - Closed: Normal operation
    - Open: Failing, no requests allowed
    - Half-Open: Testing recovery with limited requests
    """
    failure_threshold: int = 5
    reset_timeout: int = 300  # seconds
    half_open_requests: int = 3

@dataclass
class KeyPolicy:
    """
    Comprehensive API key policy configuration.
    
    Combines multiple security layers:
    1. Basic rate limiting and concurrency control
    2. Resource access restrictions
    3. Compliance requirements
    4. Security controls
    5. Usage quotas
    6. Time-based access
    7. Circuit breaker protection
    
    Implementation Notes:
    - Resource restrictions use both allowlist and denylist for flexibility
    - Time windows support multiple schedules per policy
    - Metadata and tags support custom policy management
    
    Example:
    ```python
    policy = KeyPolicy(
        type=KeyType.SERVICE,
        rate_limit=1000,
        allowed_paths={"/api/v1/*"},
        compliance=ComplianceRequirements(audit_level="standard")
    )
    ```
    """
    type: KeyType
    
    # Basic restrictions
    rate_limit: int = 1000           # Requests per hour
    burst_limit: int = 100           # Max burst size
    max_parallel: int = 10           # Max concurrent requests
    
    # Resource access
    allowed_paths: Optional[Set[str]] = None   # Allowed API paths
    allowed_methods: Optional[Set[str]] = None # Allowed HTTP methods
    allowed_resources: Optional[Set[ResourceType]] = None
    denied_resources: Optional[Set[ResourceType]] = None
    
    # Advanced controls
    compliance: Optional[ComplianceRequirements] = None
    security: Optional[SecurityControls] = None
    quota: Optional[ResourceQuota] = None
    time_windows: Optional[List[TimeWindow]] = None
    circuit_breaker: Optional[CircuitBreaker] = None
    
    # Metadata
    metadata: Optional[Metadata] = None
    tags: Optional[Dict[str, str]] = None
    
    def validate(self) -> List[str]:
        """
        Validates policy configuration for consistency and security.
        
        Checks:
        - Rate limit validity and burst limit consistency
        - Resource access conflicts
        - Time window validity
        - Security requirement compatibility
        
        Returns:
            List of validation issues (empty if valid)
        
        NOTE: This validation focuses on logical consistency but cannot
        guarantee security. Additional runtime checks are required.
        """
        issues = []
        
        # Check rate limits
        if self.rate_limit <= 0:
            issues.append("Rate limit must be positive")
        if self.burst_limit > self.rate_limit:
            issues.append("Burst limit cannot exceed rate limit")
        
        # Check resource restrictions
        if (self.allowed_resources and self.denied_resources and 
            set(self.allowed_resources) & set(self.denied_resources)):
            issues.append("Resource cannot be both allowed and denied")
        
        # Check time windows
        if self.time_windows:
            for window in self.time_windows:
                if window.start_time >= window.end_time:
                    issues.append(
                        f"Invalid time window: {window.start_time} >= {window.end_time}"
                    )
                if not 0 <= min(window.days) <= max(window.days) <= 6:
                    issues.append("Invalid days in time window")
        
        # Check compliance requirements
        if self.compliance:
            if (self.compliance.encryption_required and 
                not self.security.require_https):
                issues.append("HTTPS required when encryption is required")
        
        return issues

# Pre-defined policy templates
# NOTE: These templates should be used as starting points and customized
# based on specific security requirements

# Analytics access optimized for reporting and data analysis
# with appropriate compliance controls
ANALYTICS_POLICY = KeyPolicy(
    type=KeyType.ANALYTICS,
    rate_limit=5000,
    allowed_paths={"/api/v1/analytics/*", "/api/v1/reports/*"},
    allowed_methods={"GET"},
    compliance=ComplianceRequirements(
        audit_level="detailed",
        data_classification="internal"
    )
)

# Emergency access with enhanced security and audit controls
# typically used for incident response
EMERGENCY_POLICY = KeyPolicy(
    type=KeyType.EMERGENCY,
    rate_limit=10000,
    burst_limit=1000,
    compliance=ComplianceRequirements(
        require_mfa=True,
        audit_level="full",
        data_classification="restricted"
    ),
    security=SecurityControls(
        require_https=True,
        require_client_certs=True
    ),
    circuit_breaker=CircuitBreaker(
        failure_threshold=3,
        reset_timeout=300
    )
)

# Time-limited access with business hours restriction
# suitable for temporary contractors or limited engagements
TEMPORARY_POLICY = KeyPolicy(
    type=KeyType.TEMPORARY,
    rate_limit=100,
    burst_limit=10,
    time_windows=[
        TimeWindow(
            start_time=time(9, 0),
            end_time=time(17, 0),
            days={0, 1, 2, 3, 4},  # Monday-Friday
            timezone="UTC"
        )
    ],
    quota=ResourceQuota(
        daily_requests=1000,
        storage_mb=100
    )
) 