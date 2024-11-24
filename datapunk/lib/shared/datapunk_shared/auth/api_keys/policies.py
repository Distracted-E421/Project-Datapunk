"""
API key policy management and validation.

This module defines the policies that control API key behavior including:
- Access levels and permissions
- Rate limiting and quotas
- Resource restrictions
- Compliance requirements
- Security controls
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
    """Types of API keys with different access levels."""
    ADMIN = "admin"          # Full access
    SERVICE = "service"      # Service-to-service
    READ_ONLY = "read_only"  # Read-only access
    LIMITED = "limited"      # Limited scope access
    ANALYTICS = "analytics"  # Analytics access only
    TEMPORARY = "temporary"  # Time-limited access
    EMERGENCY = "emergency"  # Emergency access
    GEO_RESTRICTED = "geo_restricted"  # Geographically restricted

@dataclass
class ComplianceRequirements:
    """Compliance requirements for key usage."""
    encryption_required: bool = False
    audit_level: str = "standard"  # minimal, standard, full
    require_mfa: bool = False
    data_classification: str = "public"  # public, internal, confidential, restricted
    geo_restrictions: Optional[Set[str]] = None  # ISO country codes

@dataclass
class SecurityControls:
    """Security controls for key usage."""
    require_https: bool = True
    allowed_cipher_suites: Optional[Set[str]] = None
    min_tls_version: str = "1.2"
    require_client_certs: bool = False
    ip_whitelist: Optional[Set[str]] = None
    allowed_domains: Optional[Set[str]] = None

@dataclass
class ResourceQuota:
    """Resource quotas for key usage."""
    daily_requests: int = 10000
    concurrent_requests: int = 10
    storage_mb: Optional[int] = None
    compute_minutes: Optional[int] = None
    bandwidth_mb: Optional[int] = None

@dataclass
class TimeWindow:
    """Time window for allowed access."""
    start_time: time
    end_time: time
    days: Set[int]  # 0=Monday, 6=Sunday
    timezone: str = "UTC"

@dataclass
class CircuitBreaker:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    reset_timeout: int = 300  # seconds
    half_open_requests: int = 3

@dataclass
class KeyPolicy:
    """Comprehensive policy for API key usage and restrictions."""
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
        """Validate policy configuration."""
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