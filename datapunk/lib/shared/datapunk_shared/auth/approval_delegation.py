from typing import Dict, List, Optional, Set
import structlog
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from .policy_approval import ApprovalLevel
from ..exceptions import DelegationError

logger = structlog.get_logger()

class DelegationType(Enum):
    """Types of approval delegation."""
    TEMPORARY = "temporary"  # Time-limited delegation
    PERMANENT = "permanent"  # Permanent delegation
    CONDITIONAL = "conditional"  # Condition-based delegation

@dataclass
class DelegationRule:
    """Rule for approval delegation."""
    delegator_id: str
    delegate_id: str
    level: ApprovalLevel
    type: DelegationType
    conditions: Optional[Dict] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = datetime.utcnow()

class DelegationManager:
    """Manages approval delegation rules."""
    
    def __init__(self, cache_client, metrics_client):
        self.cache = cache_client
        self.metrics = metrics_client
        self.logger = logger.bind(component="delegation")
    
    async def create_delegation(self,
                              rule: DelegationRule) -> bool:
        """Create new delegation rule."""
        try:
            # Validate delegation
            await self._validate_delegation(rule)
            
            # Store delegation rule
            key = f"delegation:{rule.delegator_id}:{rule.delegate_id}"
            await self.cache.set(
                key,
                {
                    "level": rule.level.value,
                    "type": rule.type.value,
                    "conditions": rule.conditions,
                    "expires_at": rule.expires_at.isoformat() if rule.expires_at else None,
                    "created_at": rule.created_at.isoformat()
                }
            )
            
            # Update metrics
            self.metrics.increment(
                "delegations_created",
                {"type": rule.type.value}
            )
            
            return True
            
        except Exception as e:
            self.logger.error("delegation_creation_failed",
                            error=str(e))
            raise DelegationError(f"Failed to create delegation: {str(e)}")
    
    async def check_delegation(self,
                             delegator_id: str,
                             delegate_id: str,
                             level: ApprovalLevel) -> bool:
        """Check if delegation exists and is valid."""
        try:
            key = f"delegation:{delegator_id}:{delegate_id}"
            rule_data = await self.cache.get(key)
            
            if not rule_data:
                return False
            
            # Check expiration
            if rule_data.get("expires_at"):
                expires_at = datetime.fromisoformat(rule_data["expires_at"])
                if datetime.utcnow() > expires_at:
                    await self.revoke_delegation(delegator_id, delegate_id)
                    return False
            
            # Check level
            rule_level = ApprovalLevel(rule_data["level"])
            if rule_level.value < level.value:
                return False
            
            # Check conditions if any
            conditions = rule_data.get("conditions")
            if conditions and not self._evaluate_conditions(conditions):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error("delegation_check_failed",
                            error=str(e))
            return False
    
    async def revoke_delegation(self,
                              delegator_id: str,
                              delegate_id: str) -> bool:
        """Revoke delegation rule."""
        try:
            key = f"delegation:{delegator_id}:{delegate_id}"
            await self.cache.delete(key)
            
            self.metrics.increment("delegations_revoked")
            return True
            
        except Exception as e:
            self.logger.error("delegation_revocation_failed",
                            error=str(e))
            return False
    
    async def get_delegations(self,
                            delegator_id: str) -> List[DelegationRule]:
        """Get all active delegations for a delegator."""
        try:
            pattern = f"delegation:{delegator_id}:*"
            keys = await self.cache.keys(pattern)
            
            delegations = []
            for key in keys:
                data = await self.cache.get(key)
                if data:
                    delegate_id = key.split(":")[-1]
                    delegations.append(
                        DelegationRule(
                            delegator_id=delegator_id,
                            delegate_id=delegate_id,
                            level=ApprovalLevel(data["level"]),
                            type=DelegationType(data["type"]),
                            conditions=data.get("conditions"),
                            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
                            created_at=datetime.fromisoformat(data["created_at"])
                        )
                    )
            
            return delegations
            
        except Exception as e:
            self.logger.error("delegation_fetch_failed",
                            error=str(e))
            return []
    
    async def _validate_delegation(self, rule: DelegationRule) -> None:
        """Validate delegation rule."""
        # Check for circular delegation
        if await self.check_delegation(rule.delegate_id, rule.delegator_id, rule.level):
            raise DelegationError("Circular delegation detected")
        
        # Check delegation limits
        existing = await self.get_delegations(rule.delegator_id)
        if len(existing) >= 5:  # Maximum 5 active delegations
            raise DelegationError("Maximum delegation limit reached")
        
        # Validate conditions if any
        if rule.conditions:
            if not self._validate_conditions(rule.conditions):
                raise DelegationError("Invalid delegation conditions")
    
    def _validate_conditions(self, conditions: Dict) -> bool:
        """Validate delegation conditions."""
        required_fields = {"type", "value"}
        return all(
            isinstance(c, dict) and required_fields.issubset(c.keys())
            for c in conditions
        )
    
    def _evaluate_conditions(self, conditions: Dict) -> bool:
        """Evaluate delegation conditions."""
        # Implementation would depend on condition types
        # This is a placeholder
        return True 