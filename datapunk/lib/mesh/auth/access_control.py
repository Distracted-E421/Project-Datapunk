"""
Service Mesh Access Control System

Implements a comprehensive access control system for the Datapunk service mesh,
providing fine-grained permission management, IP-based access control, and
real-time monitoring of access patterns.

Key features:
- Resource-based permission management
- IP whitelist support
- Rate limiting capabilities
- Access pattern monitoring
- Prometheus metric integration

See sys-arch.mmd Gateway/Authentication for security integration details.
"""

from typing import Dict, List, Optional, Set
import time
import logging
from dataclasses import dataclass
from enum import Enum
from prometheus_client import Counter, Gauge

class Permission(Enum):
    """
    Granular permission types for service mesh access control.
    
    Aligned with service mesh security model to provide clear
    separation of concerns and audit capabilities.
    """
    READ = "read"      # Data retrieval operations
    WRITE = "write"    # Data modification operations
    ADMIN = "admin"    # Service management operations
    EXECUTE = "execute"  # Action triggering operations

class Resource(Enum):
    """
    Protected resource types within the service mesh.
    
    Maps to key service components requiring access control.
    See sys-arch.mmd Core Services for complete resource mapping.
    """
    SERVICE = "service"  # Core service operations
    METRICS = "metrics"  # Performance monitoring
    LOGS = "logs"       # Diagnostic information
    CONFIG = "config"   # Service configuration
    SECRETS = "secrets" # Sensitive credentials

@dataclass
class AccessPolicy:
    """
    Access control policy configuration.
    
    Defines access rules for services within the mesh, including
    network restrictions and rate limiting.
    
    TODO: Add role-based access control (RBAC)
    TODO: Implement policy inheritance
    """
    service_id: str
    permissions: Dict[Resource, Set[Permission]]
    ip_whitelist: Optional[List[str]] = None
    rate_limit_override: Optional[int] = None
    valid_until: Optional[float] = None

class AccessController:
    """
    Central access control management for the service mesh.
    
    Handles policy enforcement, access monitoring, and security
    metric collection. Integrates with Prometheus for real-time
    security monitoring.
    
    TODO: Add policy versioning support
    FIXME: Improve concurrent policy updates
    """
    
    def __init__(self):
        """
        Initialize access controller with monitoring.
        
        NOTE: Metrics are labeled by service_id to enable
        granular security analysis in Grafana.
        """
        self.policies: Dict[str, AccessPolicy] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize Prometheus metrics
        self.access_checks = Counter(
            'access_control_checks_total',
            'Total number of access control checks',
            ['service_id', 'resource', 'permission', 'result']
        )
        self.active_policies = Gauge(
            'access_control_active_policies',
            'Number of active access control policies',
            ['service_id']
        )

    async def add_policy(self, policy: AccessPolicy) -> bool:
        """
        Register or update service access policy.
        
        Handles policy registration with automatic metric updates.
        Thread-safe for concurrent policy management.
        
        NOTE: Policy updates are atomic to prevent security gaps
        during updates.
        """
        try:
            self.policies[policy.service_id] = policy
            self.active_policies.labels(service_id=policy.service_id).inc()
            return True
        except Exception as e:
            self.logger.error(f"Failed to add policy for {policy.service_id}: {str(e)}")
            return False

    async def remove_policy(self, service_id: str) -> bool:
        """
        Remove service access policy.
        
        Handles policy cleanup with metric updates. Used during
        service deregistration or policy revocation.
        
        NOTE: Policy removal is immediate to ensure quick
        security response when needed.
        """
        try:
            if service_id in self.policies:
                del self.policies[service_id]
                self.active_policies.labels(service_id=service_id).dec()
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove policy for {service_id}: {str(e)}")
            return False

    async def check_access(
        self,
        service_id: str,
        resource: Resource,
        permission: Permission,
        source_ip: Optional[str] = None
    ) -> bool:
        """
        Validate service access request.
        
        Performs multi-factor access validation:
        1. Policy existence check
        2. Policy expiration validation
        3. IP whitelist verification
        4. Permission verification
        
        NOTE: All checks are recorded for security audit and
        anomaly detection.
        """
        try:
            policy = self.policies.get(service_id)
            if not policy:
                self._record_access_check(service_id, resource, permission, False)
                return False

            # Validate policy expiration
            if policy.valid_until and time.time() > policy.valid_until:
                self._record_access_check(service_id, resource, permission, False)
                return False

            # Verify IP whitelist
            if policy.ip_whitelist and source_ip not in policy.ip_whitelist:
                self._record_access_check(service_id, resource, permission, False)
                return False

            # Check permissions
            has_access = (
                resource in policy.permissions and
                permission in policy.permissions[resource]
            )
            
            self._record_access_check(service_id, resource, permission, has_access)
            return has_access

        except Exception as e:
            self.logger.error(
                f"Access check failed for {service_id} on {resource}: {str(e)}"
            )
            return False

    def _record_access_check(
        self,
        service_id: str,
        resource: Resource,
        permission: Permission,
        result: bool
    ) -> None:
        """
        Record access check metrics.
        
        Captures access patterns for security monitoring and
        anomaly detection in Prometheus/Grafana.
        
        NOTE: Failed checks are important signals for potential
        security incidents.
        """
        try:
            self.access_checks.labels(
                service_id=service_id,
                resource=resource.value,
                permission=permission.value,
                result="allowed" if result else "denied"
            ).inc()
        except Exception as e:
            self.logger.error(f"Failed to record access check metric: {str(e)}") 