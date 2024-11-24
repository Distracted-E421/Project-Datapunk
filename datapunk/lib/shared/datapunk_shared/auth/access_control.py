from typing import Dict, List, Optional, Set, Any
from enum import Enum
import structlog
from dataclasses import dataclass
import json
from ..cache import CacheClient
from ..monitoring import MetricsClient
from ..exceptions import AuthError

logger = structlog.get_logger()

class Permission(Enum):
    """Core system permissions."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"

@dataclass
class ResourcePolicy:
    """Policy for resource access."""
    resource_type: str
    actions: Set[Permission]
    conditions: Dict[str, Any] = None
    priority: int = 0

@dataclass
class Role:
    """Role definition with policies."""
    name: str
    policies: List[ResourcePolicy]
    parent_roles: List[str] = None
    metadata: Dict[str, Any] = None

class AccessManager:
    """Manages access control decisions."""
    
    def __init__(self,
                 cache_client: CacheClient,
                 metrics: MetricsClient):
        self.cache = cache_client
        self.metrics = metrics
        self.logger = logger.bind(component="access_control")
        
    async def check_permission(self,
                             user_id: str,
                             resource_type: str,
                             action: Permission,
                             resource_id: Optional[str] = None,
                             context: Optional[Dict] = None) -> bool:
        """Check if user has permission for action."""
        try:
            # Get user roles
            roles = await self._get_user_roles(user_id)
            if not roles:
                self.logger.warning("no_roles_found",
                                  user_id=user_id)
                return False
            
            # Get effective policies
            policies = await self._get_effective_policies(roles)
            
            # Check policies
            for policy in sorted(policies, key=lambda p: p.priority, reverse=True):
                if policy.resource_type == resource_type and action in policy.actions:
                    if await self._evaluate_conditions(policy, context):
                        self.metrics.increment(
                            "access_granted",
                            {"user": user_id, "resource": resource_type}
                        )
                        return True
            
            self.metrics.increment(
                "access_denied",
                {"user": user_id, "resource": resource_type}
            )
            return False
            
        except Exception as e:
            self.logger.error("permission_check_failed",
                            user_id=user_id,
                            resource=resource_type,
                            error=str(e))
            self.metrics.increment("access_check_errors")
            raise AuthError(f"Permission check failed: {str(e)}")
    
    async def _get_user_roles(self, user_id: str) -> List[Role]:
        """Get roles assigned to user."""
        try:
            # Try cache first
            cache_key = f"user:roles:{user_id}"
            cached = await self.cache.get(cache_key)
            if cached:
                return [Role(**r) for r in json.loads(cached)]
            
            # TODO: Fetch from persistent storage
            return []
            
        except Exception as e:
            self.logger.error("role_fetch_failed",
                            user_id=user_id,
                            error=str(e))
            raise
    
    async def _get_effective_policies(self, roles: List[Role]) -> List[ResourcePolicy]:
        """Get effective policies including inherited ones."""
        policies = set()
        processed_roles = set()
        
        async def process_role(role: Role):
            if role.name in processed_roles:
                return
            processed_roles.add(role.name)
            
            # Add direct policies
            policies.update(role.policies)
            
            # Process parent roles
            if role.parent_roles:
                for parent_name in role.parent_roles:
                    parent = await self._get_role(parent_name)
                    if parent:
                        await process_role(parent)
        
        for role in roles:
            await process_role(role)
        
        return list(policies)
    
    async def _evaluate_conditions(self,
                                 policy: ResourcePolicy,
                                 context: Optional[Dict]) -> bool:
        """Evaluate ABAC conditions."""
        if not policy.conditions or not context:
            return True
            
        try:
            for key, expected in policy.conditions.items():
                actual = context.get(key)
                
                # Handle different condition types
                if isinstance(expected, (list, set)):
                    if actual not in expected:
                        return False
                elif isinstance(expected, dict):
                    if not self._evaluate_dict_condition(expected, actual):
                        return False
                elif actual != expected:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error("condition_evaluation_failed",
                            conditions=policy.conditions,
                            error=str(e))
            return False
    
    def _evaluate_dict_condition(self, condition: Dict, value: Any) -> bool:
        """Evaluate dictionary-based conditions."""
        for op, expected in condition.items():
            if op == "gt" and not (value > expected):
                return False
            elif op == "lt" and not (value < expected):
                return False
            elif op == "gte" and not (value >= expected):
                return False
            elif op == "lte" and not (value <= expected):
                return False
            elif op == "in" and value not in expected:
                return False
            elif op == "contains" and expected not in value:
                return False
        return True
    
    async def _get_role(self, role_name: str) -> Optional[Role]:
        """Get role by name."""
        try:
            cache_key = f"role:{role_name}"
            cached = await self.cache.get(cache_key)
            if cached:
                return Role(**json.loads(cached))
            
            # TODO: Fetch from persistent storage
            return None
            
        except Exception as e:
            self.logger.error("role_fetch_failed",
                            role=role_name,
                            error=str(e))
            raise 