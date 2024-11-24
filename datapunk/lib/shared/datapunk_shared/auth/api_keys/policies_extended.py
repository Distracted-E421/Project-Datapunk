from enum import Enum
from typing import Set, Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import time

class ResourceType(Enum):
    """Resource types for fine-grained access control."""
    DATA = "data"           # Data access
    COMPUTE = "compute"     # Computation resources
    STORAGE = "storage"     # Storage operations
    ANALYTICS = "analytics" # Analytics operations
    STREAM = "stream"       # Stream processing
    MODEL = "model"         # ML model access
    ADMIN = "admin"         # Administrative actions

@dataclass
class CompliancePolicy:
    """Compliance-specific policy requirements."""
    data_classification: str  # e.g., "public", "confidential", "restricted"
    encryption_required: bool = True
    audit_level: str = "full"  # "minimal", "standard", "full"
    retention_period: int = 90  # days
    geo_restrictions: Optional[Set[str]] = None

@dataclass
class ResourceQuota:
    """Resource usage quotas."""
    requests_per_day: int = 10000
    data_transfer_mb: int = 1000
    storage_mb: int = 5000
    compute_minutes: int = 60
    concurrent_connections: int = 10

@dataclass
class TimeWindow:
    """Time-based access restrictions."""
    start_time: time
    end_time: time
    days: Set[int]  # 0=Monday, 6=Sunday
    timezone: str = "UTC"

@dataclass
class AdvancedKeyPolicy:
    """Enhanced API key policy with advanced controls."""
    # Base settings
    type: KeyType
    rate_limit: int = 1000
    burst_limit: int = 100
    max_parallel: int = 10
    
    # Access control
    allowed_resources: Set[ResourceType] = None
    denied_resources: Set[ResourceType] = None
    ip_whitelist: Set[str] = None
    geo_restrictions: Set[str] = None
    
    # Resource management
    quota: ResourceQuota = None
    time_windows: List[TimeWindow] = None
    
    # Security
    compliance: CompliancePolicy = None
    require_mfa: bool = False
    encryption_level: str = "standard"  # "standard", "high", "military"
    
    # Monitoring
    alert_threshold: Optional[int] = None  # Trigger alert after N failures
    monitoring_level: str = "standard"  # "minimal", "standard", "debug"
    
    # Circuit breaker
    failure_threshold: int = 5
    recovery_timeout: int = 300
    half_open_limit: int = 3

class SpecializedPolicies:
    """Pre-configured policy templates."""
    
    @staticmethod
    def create_ml_policy() -> AdvancedKeyPolicy:
        """Policy for ML model access."""
        return AdvancedKeyPolicy(
            type=KeyType.SERVICE,
            rate_limit=500,
            allowed_resources={
                ResourceType.MODEL,
                ResourceType.COMPUTE
            },
            quota=ResourceQuota(
                compute_minutes=120,
                data_transfer_mb=5000
            ),
            compliance=CompliancePolicy(
                data_classification="restricted",
                encryption_required=True
            )
        )
    
    @staticmethod
    def create_analytics_policy() -> AdvancedKeyPolicy:
        """Policy for analytics access."""
        return AdvancedKeyPolicy(
            type=KeyType.ANALYTICS,
            rate_limit=2000,
            allowed_resources={
                ResourceType.ANALYTICS,
                ResourceType.DATA
            },
            quota=ResourceQuota(
                requests_per_day=50000,
                data_transfer_mb=10000
            ),
            time_windows=[
                TimeWindow(
                    start_time=time(0, 0),
                    end_time=time(23, 59),
                    days={0, 1, 2, 3, 4}  # Weekdays only
                )
            ]
        )
    
    @staticmethod
    def create_emergency_policy() -> AdvancedKeyPolicy:
        """Policy for emergency access."""
        return AdvancedKeyPolicy(
            type=KeyType.EMERGENCY,
            rate_limit=10000,
            allowed_resources=set(ResourceType),  # All resources
            require_mfa=True,
            monitoring_level="debug",
            alert_threshold=1,  # Alert on first use
            compliance=CompliancePolicy(
                audit_level="full",
                retention_period=365
            )
        ) 