from typing import Dict, List, Optional, Set, TYPE_CHECKING
import structlog
from dataclasses import dataclass
from datetime import datetime

from .types import (
    AccessContext, AccessResult, AccessLevel,
    ResourceType, UserID, RoleID, ResourceID
)
from ..types import Result, Metadata
from ..core.exceptions import AccessControlError

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....cache import CacheClient

logger = structlog.get_logger()

@dataclass
class AccessPolicy:
    """Access control policy definition."""
    resource_type: ResourceType
    access_level: AccessLevel
    roles: Set[RoleID]
    conditions: Optional[Dict] = None
    priority: int = 0
    metadata: Optional[Metadata] = None

class AccessManager:
    """Manages access control decisions."""
    
    def __init__(self,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient'):
        self.cache = cache_client
        self.metrics = metrics
        self.logger = logger.bind(component="access_control")
        self.policies: Dict[str, AccessPolicy] = {}
    
    async def check_access(self,
                          context: AccessContext) -> AccessResult:
        """Check if access is allowed."""
        try:
            # Get applicable policies
            policies = await self._get_applicable_policies(
                context.resource_type,
                context.roles
            )
            
            if not policies:
                return AccessResult(
                    allowed=False,
                    reason="No applicable policies found"
                )
            
            # Evaluate policies in priority order
            for policy in sorted(policies, key=lambda p: p.priority, reverse=True):
                result = await self._evaluate_policy(policy, context)
                if result.allowed:
                    return result
            
            # No policies allowed access
            return AccessResult(
                allowed=False,
                reason="Access denied by all applicable policies"
            )
            
        except Exception as e:
            self.logger.error("access_check_failed",
                            error=str(e),
                            context=vars(context))
            raise AccessControlError(f"Access check failed: {str(e)}")
    
    async def add_policy(self,
                        policy: AccessPolicy) -> Result:
        """Add a new access policy."""
        try:
            # Validate policy
            if not self._validate_policy(policy):
                return {
                    "success": False,
                    "error": "Invalid policy configuration"
                }
            
            # Store policy
            policy_id = self._generate_policy_id(policy)
            self.policies[policy_id] = policy
            
            # Update metrics
            self.metrics.increment(
                "access_policies_added",
                {
                    "resource_type": policy.resource_type.value,
                    "access_level": policy.access_level.value
                }
            )
            
            return {
                "success": True,
                "policy_id": policy_id
            }
            
        except Exception as e:
            self.logger.error("policy_addition_failed",
                            error=str(e))
            raise AccessControlError(f"Failed to add policy: {str(e)}")
    
    async def _get_applicable_policies(self,
                                     resource_type: ResourceType,
                                     roles: List[RoleID]) -> List[AccessPolicy]:
        """Get policies applicable to resource and roles."""
        return [
            policy for policy in self.policies.values()
            if (policy.resource_type == resource_type and
                any(role in policy.roles for role in roles))
        ]
    
    async def _evaluate_policy(self,
                             policy: AccessPolicy,
                             context: AccessContext) -> AccessResult:
        """Evaluate a single policy."""
        try:
            # Check basic access level
            if context.access_level.value > policy.access_level.value:
                return AccessResult(
                    allowed=False,
                    reason="Insufficient access level"
                )
            
            # Check conditions if any
            if policy.conditions:
                if not await self._evaluate_conditions(
                    policy.conditions,
                    context
                ):
                    return AccessResult(
                        allowed=False,
                        reason="Conditions not met"
                    )
            
            # Access allowed
            return AccessResult(
                allowed=True,
                context={
                    "policy_id": self._generate_policy_id(policy),
                    "granted_at": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error("policy_evaluation_failed",
                            error=str(e))
            return AccessResult(
                allowed=False,
                reason=f"Evaluation error: {str(e)}"
            )
    
    def _validate_policy(self, policy: AccessPolicy) -> bool:
        """Validate policy configuration."""
        if not policy.roles:
            return False
        if not isinstance(policy.resource_type, ResourceType):
            return False
        if not isinstance(policy.access_level, AccessLevel):
            return False
        return True
    
    def _generate_policy_id(self, policy: AccessPolicy) -> str:
        """Generate unique policy ID."""
        return (f"{policy.resource_type.value}_"
                f"{policy.access_level.value}_"
                f"{datetime.utcnow().timestamp()}")
    
    async def _evaluate_conditions(self,
                                 conditions: Dict,
                                 context: AccessContext) -> bool:
        """Evaluate policy conditions."""
        # Implementation would evaluate custom conditions
        # This is a placeholder
        return True