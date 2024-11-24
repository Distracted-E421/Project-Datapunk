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
    """
    Defines an access control policy for resources.
    
    This class implements a Role-Based Access Control (RBAC) policy with additional
    support for conditional access rules. Policies are evaluated in priority order,
    with higher priority policies taking precedence.
    
    NOTE: Conditions are optional and can be used to implement fine-grained
    access control based on context-specific rules.
    """
    resource_type: ResourceType
    access_level: AccessLevel
    roles: Set[RoleID]
    conditions: Optional[Dict] = None  # Custom rules for fine-grained access control
    priority: int = 0  # Higher values indicate higher priority in evaluation order
    metadata: Optional[Metadata] = None  # Additional policy-specific data

class AccessManager:
    """
    Central manager for access control decisions using policy-based evaluation.
    
    This class implements a hierarchical access control system that:
    1. Evaluates multiple policies in priority order
    2. Supports conditional access rules
    3. Provides caching and metrics for performance monitoring
    
    IMPORTANT: Access decisions are "deny by default" - access is only granted if
    explicitly allowed by at least one applicable policy.
    """
    
    def __init__(self,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient'):
        self.cache = cache_client
        self.metrics = metrics
        self.logger = logger.bind(component="access_control")
        self.policies: Dict[str, AccessPolicy] = {}
    
    async def check_access(self,
                          context: AccessContext) -> AccessResult:
        """
        Evaluates access request against applicable policies.
        
        The evaluation process:
        1. Retrieves policies matching the resource type and user roles
        2. Evaluates policies in priority order (highest first)
        3. Returns on first allowing policy or denies if none allow
        
        NOTE: This method implements fail-closed behavior - any errors during
        evaluation will result in denied access.
        """
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
        """
        Registers a new access policy in the system.
        
        IMPORTANT: Policy IDs are generated automatically based on resource type,
        access level, and timestamp to ensure uniqueness.
        
        TODO: Consider adding policy conflict detection to prevent contradictory rules
        """
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
        """
        Filters policies applicable to the given resource and roles.
        
        NOTE: A policy is considered applicable if:
        1. It matches the requested resource type
        2. It grants access to at least one of the user's roles
        
        TODO: Consider caching frequently accessed policy combinations
        """
        return [
            policy for policy in self.policies.values()
            if (policy.resource_type == resource_type and
                any(role in policy.roles for role in roles))
        ]
    
    async def _evaluate_policy(self,
                             policy: AccessPolicy,
                             context: AccessContext) -> AccessResult:
        """
        Evaluates a single policy against the access context.
        
        The evaluation hierarchy is:
        1. Check basic access level requirements
        2. Evaluate additional conditions if present
        
        IMPORTANT: Any errors during condition evaluation result in denied access
        to maintain security.
        """
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
        """
        Validates policy configuration for correctness.
        
        FIXME: Add validation for condition structure when custom conditions
        are implemented.
        
        NOTE: Current validation checks:
        - Non-empty roles set
        - Valid resource type
        - Valid access level
        """
        if not policy.roles:
            return False
        if not isinstance(policy.resource_type, ResourceType):
            return False
        if not isinstance(policy.access_level, AccessLevel):
            return False
        return True
    
    def _generate_policy_id(self, policy: AccessPolicy) -> str:
        """
        Generates a unique policy identifier.
        
        Format: {resource_type}_{access_level}_{timestamp}
        
        NOTE: While timestamp ensures uniqueness, consider implementing a more
        structured ID generation system for better policy management.
        """
        return (f"{policy.resource_type.value}_"
                f"{policy.access_level.value}_"
                f"{datetime.utcnow().timestamp()}")
    
    async def _evaluate_conditions(self,
                                 conditions: Dict,
                                 context: AccessContext) -> bool:
        """
        Evaluates custom policy conditions.
        
        TODO: Implement actual condition evaluation logic. Current implementation
        is a placeholder that always returns True.
        
        Potential conditions might include:
        - Time-based access rules
        - Resource ownership checks
        - Custom business logic
        """
        # Implementation would evaluate custom conditions
        # This is a placeholder
        return True