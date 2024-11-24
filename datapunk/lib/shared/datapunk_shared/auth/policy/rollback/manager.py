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
    """
    Represents an immutable snapshot of a policy's state for potential rollback operations.
    
    This class captures the complete state needed to restore a policy to a previous version,
    including metadata about the change and affected access keys for impact analysis.
    """
    timestamp: datetime
    policy_id: str  # Format: {policy_type}_{unix_timestamp}
    policy_type: PolicyType
    old_policy: Dict  # Complete policy state before changes
    affected_keys: List[str]  # Access keys impacted by policy changes
    metadata: Optional[Dict] = None  # Additional context about the policy change

class RollbackManager:
    """
    Manages the versioning and restoration of security policies with safety validations.
    
    This manager implements a rolling history of policy changes, allowing controlled rollbacks
    while ensuring system stability through validation checks. It uses a cache-based storage
    system for performance and maintains a fixed-size history to prevent unbounded growth.
    
    Key features:
    - Atomic rollback point creation
    - Pre-rollback validation
    - Automatic history cleanup
    - Metrics tracking for operational monitoring
    """
    
    def __init__(self,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient',
                 validator: RollbackValidator,
                 max_history: int = 10):
        """
        Initialize the rollback manager with required dependencies and configuration.
        
        Args:
            cache_client: Handles persistent storage of rollback points
            metrics: Tracks operational metrics for monitoring
            validator: Performs safety checks before rollbacks
            max_history: Maximum number of rollback points to retain per policy type
        """
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
        """
        Creates a safety snapshot before policy modifications.
        
        IMPORTANT: This method must be called BEFORE making any policy changes
        to ensure accurate rollback capabilities.
        
        Returns:
            str: Unique identifier for the rollback point
            
        Raises:
            AuthError: If rollback point creation fails
        """
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
        """
        Performs safety validation before allowing a rollback operation.
        
        Validates that rolling back to a previous policy state won't create
        security vulnerabilities or break existing access patterns.
        
        NOTE: This is a pre-check only - actual rollback must be handled separately
        after validation passes.
        
        Returns:
            RollbackValidationResult: Contains validation status and potential risks
            
        Raises:
            AuthError: If rollback point doesn't exist
        """
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
        """
        Persists rollback point data using a two-part storage strategy:
        1. Stores complete point data with a unique key
        2. Maintains an ordered history list for each policy type
        
        Cache key structure:
        - Point data: policy:rollback:point:{policy_id}
        - History list: policy:rollback:history:{policy_type}
        """
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
        """
        Enforces history size limits to prevent unbounded cache growth.
        
        IMPORTANT: This operation modifies the history list but does not remove
        the actual rollback point data. This is intentional to allow reference
        to historical points even after they're removed from the active history.
        """
        history_key = f"policy:rollback:history:{policy_type}"
        history_list = await self.cache.lrange(history_key, 0, self.max_history - 1)
        if len(history_list) > self.max_history:
            await self.cache.ltrim(history_key, self.max_history, -1)
    
    async def _get_rollback_point(self, policy_id: str) -> Optional[RollbackPoint]:
        """
        Retrieves and reconstructs a RollbackPoint from cached data.
        
        NOTE: Returns None if point doesn't exist rather than raising an exception
        to allow for existence checking.
        """
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
        """
        Fetches the active policy configuration for comparison during validation.
        
        Cache key format: policy:current:{policy_type}
        
        Raises:
            AuthError: If no active policy exists for the given type
        """
        current_policy_key = f"policy:current:{policy_type.value}"
        current_policy = await self.cache.get(current_policy_key)
        if current_policy:
            return current_policy
        raise AuthError(f"Current policy for {policy_type.value} not found")