from enum import Enum
from typing import Set, Dict, Any, Optional
from dataclasses import dataclass

class KeyType(Enum):
    """Extended key types for different use cases."""
    ADMIN = "admin"              # Full system access
    SERVICE = "service"          # Service-to-service communication
    READ_ONLY = "read_only"      # Read-only access
    WRITE_ONLY = "write_only"    # Write-only access
    ANALYTICS = "analytics"      # Analytics and reporting
    AUDIT = "audit"              # Audit log access
    TEMPORARY = "temporary"      # Short-lived access
    EMERGENCY = "emergency"      # Break-glass access
    RATE_LIMITED = "rate_limited"  # Heavily rate-limited
    GEO_RESTRICTED = "geo_restricted"  # Geographic restrictions

@dataclass
class AdvancedKeyPolicy:
    """Enhanced key policy with advanced features."""
    type: KeyType
    rate_limit: int = 1000           # Requests per hour
    burst_limit: int = 100           # Max burst size
    max_parallel: int = 10           # Max concurrent requests
    ip_whitelist: Optional[Set[str]] = None  # Allowed IPs
    geo_restrictions: Optional[Set[str]] = None  # Allowed regions
    allowed_paths: Optional[Set[str]] = None  # Allowed API paths
    allowed_methods: Optional[Set[str]] = None  # Allowed HTTP methods
    require_mfa: bool = False        # Require MFA for usage
    audit_level: str = "normal"      # Audit logging level
    quota: Optional[Dict[str, int]] = None  # Usage quotas
    circuit_breaker: Optional[Dict[str, Any]] = None  # Circuit breaker config
    encryption_required: bool = True  # Require TLS
    allowed_times: Optional[Dict[str, str]] = None  # Time restrictions

# Benefits of these policy types:

# 1. Fine-grained Access Control
ANALYTICS_POLICY = AdvancedKeyPolicy(
    type=KeyType.ANALYTICS,
    rate_limit=5000,
    allowed_paths={"/api/v1/analytics/*", "/api/v1/reports/*"},
    allowed_methods={"GET"},
    audit_level="detailed"
)

# 2. Enhanced Security
EMERGENCY_POLICY = AdvancedKeyPolicy(
    type=KeyType.EMERGENCY,
    require_mfa=True,
    audit_level="full",
    encryption_required=True,
    circuit_breaker={
        "failure_threshold": 3,
        "reset_timeout": 300
    }
)

# 3. Compliance Requirements
AUDIT_POLICY = AdvancedKeyPolicy(
    type=KeyType.AUDIT,
    audit_level="full",
    encryption_required=True,
    allowed_paths={"/api/v1/audit/*"},
    require_mfa=True
)

# 4. Geographic Restrictions
GEO_POLICY = AdvancedKeyPolicy(
    type=KeyType.GEO_RESTRICTED,
    geo_restrictions={"US", "EU"},
    encryption_required=True,
    audit_level="detailed"
)

# 5. Time-based Access
TEMPORARY_POLICY = AdvancedKeyPolicy(
    type=KeyType.TEMPORARY,
    allowed_times={
        "start": "09:00",
        "end": "17:00",
        "timezone": "UTC"
    },
    audit_level="full"
)

# 6. Resource Management
RATE_LIMITED_POLICY = AdvancedKeyPolicy(
    type=KeyType.RATE_LIMITED,
    rate_limit=100,
    burst_limit=10,
    quota={
        "daily_requests": 1000,
        "storage_mb": 100
    }
) 