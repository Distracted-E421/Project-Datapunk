# This module implements fine-grained access control and compliance policies for API keys.
# It provides a flexible framework for enforcing security boundaries, resource quotas,
# and compliance requirements across different types of API access patterns.

from enum import Enum
from typing import Set, Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import time

class ResourceType(Enum):
    """
    Defines distinct resource categories for access control. This granular approach
    allows for precise permission management and helps enforce the principle of
    least privilege across different system components.
    
    NOTE: When adding new resource types, ensure corresponding policy enforcement
    logic is updated in the access control layer.
    """
    DATA = "data"           # Raw data access operations
    COMPUTE = "compute"     # CPU/GPU resource allocation
    STORAGE = "storage"     # Persistent storage operations
    ANALYTICS = "analytics" # Business intelligence and reporting
    STREAM = "stream"       # Real-time data processing
    MODEL = "model"         # ML model inference and training
    ADMIN = "admin"         # System administration capabilities

@dataclass
class CompliancePolicy:
    """
    Enforces regulatory and organizational compliance requirements.
    Used to maintain data governance standards and audit trails.
    
    NOTE: retention_period should align with relevant regulatory requirements
    (e.g., GDPR, HIPAA) based on data_classification.
    
    TODO: Add support for custom compliance frameworks and certification requirements
    """
    data_classification: str  # Maps to organization's data classification scheme
    encryption_required: bool = True
    audit_level: str = "full"  # Controls depth of audit logging
    retention_period: int = 90  # Mandatory data retention period
    geo_restrictions: Optional[Set[str]] = None  # Data sovereignty requirements

@dataclass
class ResourceQuota:
    """
    Defines usage limits to prevent resource abuse and ensure fair allocation.
    Default values are conservative and should be adjusted based on
    service tier and operational requirements.
    
    FIXME: Consider implementing dynamic quota adjustment based on usage patterns
    """
    requests_per_day: int = 10000
    data_transfer_mb: int = 1000
    storage_mb: int = 5000
    compute_minutes: int = 60
    concurrent_connections: int = 10

@dataclass
class TimeWindow:
    """
    Implements temporal access control for API keys.
    Useful for limiting access to business hours or scheduled maintenance windows.
    
    NOTE: days uses 0-6 for Monday-Sunday to align with ISO 8601 standard
    """
    start_time: time
    end_time: time
    days: Set[int]  # 0=Monday, 6=Sunday
    timezone: str = "UTC"

@dataclass
class AdvancedKeyPolicy:
    """
    Comprehensive API key policy that combines access control, resource management,
    and security requirements. Designed to support complex enterprise use cases
    while maintaining security best practices.
    
    The policy implements a defense-in-depth approach through multiple
    security controls:
    - Resource access control
    - Rate limiting and quotas
    - Geographic restrictions
    - Compliance requirements
    - Circuit breaker pattern for failure handling
    
    TODO: Add support for role-based access control (RBAC) integration
    TODO: Implement policy inheritance and override mechanisms
    """
    # Circuit breaker settings are tuned for general use
    # Adjust based on specific service reliability requirements
    failure_threshold: int = 5
    recovery_timeout: int = 300  # seconds
    half_open_limit: int = 3     # max requests in half-open state

class SpecializedPolicies:
    """
    Factory for pre-configured policy templates targeting specific use cases.
    These templates provide secure defaults while allowing customization
    for specific operational requirements.
    """
    
    @staticmethod
    def create_ml_policy() -> AdvancedKeyPolicy:
        """
        Policy optimized for machine learning workloads.
        Balances resource access for model training/inference while
        maintaining data security through encryption and access controls.
        """
        return AdvancedKeyPolicy(
            type=KeyType.SERVICE,
            rate_limit=500,  # Conservative limit to prevent resource exhaustion
            allowed_resources={
                ResourceType.MODEL,
                ResourceType.COMPUTE
            },
            quota=ResourceQuota(
                compute_minutes=120,  # Adjusted for typical model inference needs
                data_transfer_mb=5000
            ),
            compliance=CompliancePolicy(
                data_classification="restricted",
                encryption_required=True
            )
        )
    
    @staticmethod
    def create_analytics_policy() -> AdvancedKeyPolicy:
        """
        Policy for business intelligence and analytics access.
        Configured for high-throughput data access during business hours
        with appropriate quotas for reporting workloads.
        """
        return AdvancedKeyPolicy(
            type=KeyType.ANALYTICS,
            rate_limit=2000,  # Higher limit for batch processing
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
                    days={0, 1, 2, 3, 4}  # Business days only
                )
            ]
        )
    
    @staticmethod
    def create_emergency_policy() -> AdvancedKeyPolicy:
        """
        Policy for emergency/break-glass access scenarios.
        Provides elevated access with strict audit controls and
        immediate alerting to security teams.
        
        IMPORTANT: This policy should only be used in documented emergency
        procedures and requires immediate security review upon activation.
        """
        return AdvancedKeyPolicy(
            type=KeyType.EMERGENCY,
            rate_limit=10000,
            allowed_resources=set(ResourceType),  # Full system access
            require_mfa=True,
            monitoring_level="debug",
            alert_threshold=1,  # Immediate alerting on use
            compliance=CompliancePolicy(
                audit_level="full",
                retention_period=365  # Extended retention for incident review
            )
        ) 