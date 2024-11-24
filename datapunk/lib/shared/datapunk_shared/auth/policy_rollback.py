from typing import Dict, List, Optional, Any
import structlog
from dataclasses import dataclass
from datetime import datetime
from .key_policies_extended import AdvancedKeyPolicy
from ..exceptions import RollbackError
from ..monitoring import MetricsClient

logger = structlog.get_logger()

@dataclass
class RollbackPoint:
    """Snapshot of policy state for rollback."""
    timestamp: datetime
    policy_id: str
    old_policy: AdvancedKeyPolicy
    affected_keys: List[str]
    metadata: Optional[Dict] = None

class PolicyRollbackManager:
    """Manages policy rollbacks and version history."""
    
    def __init__(self,
                 cache_client,
                 metrics: MetricsClient,
                 max_history: int = 10):
        self.cache = cache_client
        self.metrics = metrics
        self.max_history = max_history
        self.logger = logger.bind(component="policy_rollback")
    
    async def create_rollback_point(self,
                                  policy: AdvancedKeyPolicy,
                                  affected_keys: List[str],
                                  metadata: Optional[Dict] = None) -> str:
        """Create a rollback point before policy changes."""
        try:
            rollback_point = RollbackPoint(
                timestamp=datetime.utcnow(),
                policy_id=f"{policy.type.value}_{datetime.utcnow().isoformat()}",
                old_policy=policy,
                affected_keys=affected_keys,
                metadata=metadata
            )
            
            # Store rollback point
            await self._store_rollback_point(rollback_point)
            
            # Maintain history limit
            await self._cleanup_history(policy.type.value)
            
            self.metrics.increment(
                "rollback_point_created",
                {"policy_type": policy.type.value}
            )
            
            return rollback_point.policy_id
            
        except Exception as e:
            self.logger.error("rollback_point_creation_failed",
                            error=str(e))
            raise RollbackError(f"Failed to create rollback point: {str(e)}")
    
    async def rollback_policy(self,
                            policy_id: str,
                            reason: str) -> bool:
        """Rollback to a previous policy state."""
        try:
            # Get rollback point
            rollback_point = await self._get_rollback_point(policy_id)
            if not rollback_point:
                raise RollbackError(f"Rollback point {policy_id} not found")
            
            self.logger.info("starting_policy_rollback",
                           policy_id=policy_id,
                           reason=reason)
            
            # Create new rollback point for current state (to allow roll-forward)
            current_policy = await self._get_current_policy(
                rollback_point.old_policy.type.value
            )
            if current_policy:
                await self.create_rollback_point(
                    current_policy,
                    rollback_point.affected_keys,
                    {"reason": "auto_backup_before_rollback"}
                )
            
            # Apply old policy to affected keys
            success = await self._apply_rollback(rollback_point)
            
            if success:
                self.metrics.increment(
                    "policy_rollback_success",
                    {"policy_type": rollback_point.old_policy.type.value}
                )
                self.logger.info("policy_rollback_complete",
                               policy_id=policy_id)
            else:
                self.metrics.increment(
                    "policy_rollback_failure",
                    {"policy_type": rollback_point.old_policy.type.value}
                )
                self.logger.error("policy_rollback_failed",
                                policy_id=policy_id)
            
            return success
            
        except Exception as e:
            self.logger.error("rollback_failed",
                            policy_id=policy_id,
                            error=str(e))
            self.metrics.increment("policy_rollback_error")
            raise RollbackError(f"Rollback failed: {str(e)}")
    
    async def get_rollback_history(self,
                                 policy_type: str) -> List[Dict]:
        """Get rollback history for policy type."""
        try:
            history_key = f"policy:rollback:history:{policy_type}"
            history = await self.cache.lrange(history_key, 0, -1)
            
            return [
                {
                    "policy_id": point.policy_id,
                    "timestamp": point.timestamp.isoformat(),
                    "metadata": point.metadata
                }
                for point in [
                    await self._get_rollback_point(pid)
                    for pid in history
                ]
                if point is not None
            ]
            
        except Exception as e:
            self.logger.error("history_fetch_failed",
                            policy_type=policy_type,
                            error=str(e))
            return []
    
    async def _store_rollback_point(self, point: RollbackPoint) -> None:
        """Store rollback point in cache."""
        # Store rollback point data
        point_key = f"policy:rollback:point:{point.policy_id}"
        await self.cache.set(
            point_key,
            {
                "timestamp": point.timestamp.isoformat(),
                "policy": vars(point.old_policy),
                "affected_keys": point.affected_keys,
                "metadata": point.metadata
            }
        )
        
        # Add to history list
        history_key = f"policy:rollback:history:{point.old_policy.type.value}"
        await self.cache.lpush(history_key, point.policy_id)
    
    async def _get_rollback_point(self,
                                policy_id: str) -> Optional[RollbackPoint]:
        """Get rollback point from cache."""
        point_key = f"policy:rollback:point:{policy_id}"
        data = await self.cache.get(point_key)
        
        if not data:
            return None
            
        return RollbackPoint(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            policy_id=policy_id,
            old_policy=AdvancedKeyPolicy(**data["policy"]),
            affected_keys=data["affected_keys"],
            metadata=data["metadata"]
        )
    
    async def _cleanup_history(self, policy_type: str) -> None:
        """Maintain history size limit."""
        history_key = f"policy:rollback:history:{policy_type}"
        
        # Trim history list
        await self.cache.ltrim(history_key, 0, self.max_history - 1)
        
        # Clean up old rollback points
        history = await self.cache.lrange(history_key, 0, -1)
        all_points = await self.cache.keys(f"policy:rollback:point:*")
        
        for point_key in all_points:
            policy_id = point_key.split(":")[-1]
            if policy_id not in history:
                await self.cache.delete(point_key)
    
    async def _get_current_policy(self,
                                policy_type: str) -> Optional[AdvancedKeyPolicy]:
        """Get current active policy."""
        current_key = f"policy:current:{policy_type}"
        data = await self.cache.get(current_key)
        return AdvancedKeyPolicy(**data) if data else None
    
    async def _apply_rollback(self, point: RollbackPoint) -> bool:
        """Apply rollback point to restore previous state."""
        try:
            # Store old policy as current
            current_key = f"policy:current:{point.old_policy.type.value}"
            await self.cache.set(current_key, vars(point.old_policy))
            
            # Update all affected keys
            for key in point.affected_keys:
                await self.cache.set(f"policy:{key}", vars(point.old_policy))
            
            return True
            
        except Exception as e:
            self.logger.error("rollback_application_failed",
                            error=str(e))
            return False 