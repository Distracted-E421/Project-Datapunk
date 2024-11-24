from typing import Dict, List, Optional, Set
import time
import logging
from dataclasses import dataclass
from enum import Enum
from prometheus_client import Counter, Gauge

class Permission(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    EXECUTE = "execute"

class Resource(Enum):
    SERVICE = "service"
    METRICS = "metrics"
    LOGS = "logs"
    CONFIG = "config"
    SECRETS = "secrets"

@dataclass
class AccessPolicy:
    service_id: str
    permissions: Dict[Resource, Set[Permission]]
    ip_whitelist: Optional[List[str]] = None
    rate_limit_override: Optional[int] = None
    valid_until: Optional[float] = None

class AccessController:
    def __init__(self):
        self.policies: Dict[str, AccessPolicy] = {}
        self.logger = logging.getLogger(__name__)
        
        # Metrics
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
        """Add or update an access policy"""
        try:
            self.policies[policy.service_id] = policy
            self.active_policies.labels(service_id=policy.service_id).inc()
            return True
        except Exception as e:
            self.logger.error(f"Failed to add policy for {policy.service_id}: {str(e)}")
            return False

    async def remove_policy(self, service_id: str) -> bool:
        """Remove an access policy"""
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
        """Check if a service has the required access"""
        try:
            policy = self.policies.get(service_id)
            if not policy:
                self._record_access_check(service_id, resource, permission, False)
                return False

            # Check policy expiration
            if policy.valid_until and time.time() > policy.valid_until:
                self._record_access_check(service_id, resource, permission, False)
                return False

            # Check IP whitelist
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
        """Record access check metrics"""
        try:
            self.access_checks.labels(
                service_id=service_id,
                resource=resource.value,
                permission=permission.value,
                result="allowed" if result else "denied"
            ).inc()
        except Exception as e:
            self.logger.error(f"Failed to record access check metric: {str(e)}") 