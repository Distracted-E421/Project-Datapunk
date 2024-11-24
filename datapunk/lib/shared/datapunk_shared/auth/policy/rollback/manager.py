from typing import Dict, List, Optional, TYPE_CHECKING
import structlog
from datetime import datetime
from dataclasses import dataclass

from .validation import RollbackValidator, RollbackValidationResult, RollbackRisk
from ..types import PolicyType, PolicyStatus
from ...core.exceptions import AuthError

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....cache import CacheClient

logger = structlog.get_logger()

@dataclass
class RollbackPoint:
    """Snapshot of policy state for rollback."""
    timestamp: datetime
    policy_id: str
    policy_type: PolicyType
    old_policy: Dict
    affected_keys: List[str]
    metadata: Optional[Dict] = None

class RollbackManager:
    """Manages policy rollbacks and version history."""
    
    def __init__(self,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient',
                 validator: RollbackValidator,
                 max_history: int = 10):
        self.cache = cache_client
        self.metrics = metrics
        self.validator = validator
        self.max_history = max_history
        self.logger = logger.bind(component="rollback_manager")
    
    async def create_rollback_point(self,
                                  policy: Dict,
                                  policy_type: PolicyType,
                                  affected_keys: List[str],
                                  metadata: Optional[Dict] = None) -> str:
        """Create a rollback point before policy changes."""
        try:
            rollback_point = RollbackPoint(
                timestamp=datetime.utcnow(),
                policy_id=f"{policy_type.value}_{datetime.utcnow().timestamp()}",
                policy_type=policy_type,
                old_policy=policy,
                affected_keys=affected_keys,
                metadata=metadata
            )
            
            # Store rollback point
            await self._store_rollback_point(rollback_point)
            
            # Maintain history limit
            await self._cleanup_history(policy_type.value)
            
            self.metrics.increment(
                "rollback_point_created",
                {"policy_type": policy_type.value}
            )
            
            return rollback_point.policy_id
            
        except Exception as e:
            self.logger.error("rollback_point_creation_failed",
                            error=str(e))
            raise AuthError(f"Failed to create rollback point: {str(e)}")
    
    async def validate_rollback(self,
                              policy_id: str) -> RollbackValidationResult:
        """Validate a potential rollback operation."""
        try:
            rollback_point = await self._get_rollback_point(policy_id)
            if not rollback_point:
                raise AuthError(f"Rollback point {policy_id} not found")
            
            current_policy = await self._get_current_policy(
                rollback_point.policy_type
            )
            
            return await self.validator.validate_rollback(
                current_policy=current_policy,
                rollback_policy=rollback_point.old_policy,
                affected_keys=rollback_point.affected_keys
            )
            
        except Exception as e:
            self.logger.error("rollback_validation_failed",
                            policy_id=policy_id,
                            error=str(e))
            raise
    
    async def _store_rollback_point(self, point: RollbackPoint) -> None:
        """Store rollback point in cache."""
        # Store rollback point data
        point_key = f"policy:rollback:point:{point.policy_id}"
        await self.cache.set(
            point_key,
            {
                "timestamp": point.timestamp.isoformat(),
                "policy_type": point.policy_type.value,
                "policy": point.old_policy,
                "affected_keys": point.affected_keys,
                "metadata": point.metadata
            }
        )
        
        # Add to history list
        history_key = f"policy:rollback:history:{point.policy_type.value}"
        await self.cache.lpush(history_key, point.policy_id)
    
    async def _cleanup_history(self, policy_type: str) -> None:
        """Cleanup history list to maintain the maximum history limit."""
        history_key = f"policy:rollback:history:{policy_type}"
        history_list = await self.cache.lrange(history_key, 0, self.max_history - 1)
        if len(history_list) > self.max_history:
            await self.cache.ltrim(history_key, self.max_history, -1)
    
    async def _get_rollback_point(self, policy_id: str) -> Optional[RollbackPoint]:
        """Retrieve a rollback point from cache."""
        point_key = f"policy:rollback:point:{policy_id}"
        point_data = await self.cache.get(point_key)
        if point_data:
            return RollbackPoint(
                timestamp=datetime.fromisoformat(point_data["timestamp"]),
                policy_id=policy_id,
                policy_type=PolicyType(point_data["policy_type"]),
                old_policy=point_data["policy"],
                affected_keys=point_data["affected_keys"],
                metadata=point_data["metadata"]
            )
        return None
    
    async def _get_current_policy(self, policy_type: PolicyType) -> Dict:
        """Retrieve the current policy from cache."""
        current_policy_key = f"policy:current:{policy_type.value}"
        current_policy = await self.cache.get(current_policy_key)
        if current_policy:
            return current_policy
        raise AuthError(f"Current policy for {policy_type.value} not found")