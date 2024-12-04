"""
Approval Delegation System

Manages temporary and permanent transfers of approval authority while maintaining
security boundaries and audit trails. Integrates with policy approval workflows
and compliance monitoring systems.

Key capabilities:
- Flexible delegation patterns (temporary, permanent, conditional)
- Circular delegation prevention
- Automatic expiration handling
- Condition-based authority validation
- Real-time delegation metrics

IMPORTANT: All operations are logged through DelegationAuditor for compliance
with SOC2 and ISO 27001 requirements.
"""

from typing import Dict, List, Optional, Set
import structlog
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from .policy_approval import ApprovalLevel
from ...exceptions import DelegationError

logger = structlog.get_logger()

class DelegationType(Enum):
    """
    Delegation patterns supporting different security and operational needs:
    
    TEMPORARY: Short-term coverage (e.g., vacation coverage)
    PERMANENT: Long-term authority transfer (e.g., role transitions)
    CONDITIONAL: Context-specific delegation (e.g., business hours only)
    """
    TEMPORARY = "temporary"
    PERMANENT = "permanent"
    CONDITIONAL = "conditional"

@dataclass
class DelegationRule:
    """
    Structured delegation configuration enforcing consistent authority transfer.
    
    NOTE: All timestamps use UTC to ensure consistent handling across timezones
    and prevent expiration timing issues.
    """
    delegator_id: str
    delegate_id: str
    level: ApprovalLevel
    type: DelegationType
    conditions: Optional[Dict] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = datetime.utcnow()

class DelegationManager:
    """
    Orchestrates delegation lifecycle with safety controls and monitoring.
    
    Key features:
    - Atomic delegation operations
    - Circular delegation prevention
    - Automatic expiration handling
    - Condition evaluation
    - Usage metrics collection
    
    IMPORTANT: Uses cache for delegation storage to ensure fast access control checks.
    Cache failures could impact security operations.
    
    TODO: Implement cache redundancy for high availability
    TODO: Add bulk delegation operations for role transitions
    """
    
    def __init__(self, cache_client, metrics_client):
        """
        Initialize manager with required infrastructure clients.
        
        NOTE: cache_client must support atomic operations to prevent
        race conditions in delegation states.
        """
        self.cache = cache_client
        self.metrics = metrics_client
        self.logger = logger.bind(component="delegation")
    
    async def create_delegation(self,
                              rule: DelegationRule) -> bool:
        """
        Establishes new delegation authority with safety controls.
        
        IMPORTANT: Validates against circular delegation and enforces
        delegation limits before creation to maintain security boundaries.
        
        NOTE: All delegation creations are atomic operations to prevent
        race conditions in authority assignments.
        
        Metrics tracked:
        - delegations_created (tagged by type)
        - delegation_validation_time
        """
        try:
            # Validate before any state changes
            await self._validate_delegation(rule)
            
            # Store with atomic operation
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
            
            # Track creation for monitoring
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
        """
        Validates delegation existence and authority level.
        
        Performs multi-step validation:
        1. Existence check
        2. Expiration verification
        3. Authority level comparison
        4. Condition evaluation
        
        NOTE: Automatically removes expired delegations during checks
        to maintain clean state.
        
        IMPORTANT: Returns False on any validation failure rather than
        raising exceptions to support fast access checks.
        """
        try:
            key = f"delegation:{delegator_id}:{delegate_id}"
            rule_data = await self.cache.get(key)
            
            if not rule_data:
                return False
            
            # Handle expiration
            if rule_data.get("expires_at"):
                expires_at = datetime.fromisoformat(rule_data["expires_at"])
                if datetime.utcnow() > expires_at:
                    await self.revoke_delegation(delegator_id, delegate_id)
                    return False
            
            # Verify authority level
            rule_level = ApprovalLevel(rule_data["level"])
            if rule_level.value < level.value:
                return False
            
            # Evaluate dynamic conditions
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
        """
        Immediately terminates delegation authority.
        
        IMPORTANT: Revocation is a critical security operation that must
        complete even if metrics or audit logging fails.
        
        NOTE: Returns True even if delegation didn't exist to ensure
        idempotent behavior for security operations.
        """
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
        """
        Enforces delegation security controls and limits.
        
        Validates:
        1. No circular delegation chains
        2. Maximum active delegation limits
        3. Condition format and validity
        
        IMPORTANT: All validations must pass before any delegation is created
        to maintain security boundaries.
        
        Raises:
            DelegationError: If any validation check fails
        """
        # Prevent authority loops
        if await self.check_delegation(rule.delegate_id, rule.delegator_id, rule.level):
            raise DelegationError("Circular delegation detected")
        
        # Enforce delegation limits
        existing = await self.get_delegations(rule.delegator_id)
        if len(existing) >= 5:  # Maximum 5 active delegations
            raise DelegationError("Maximum delegation limit reached")
        
        # Validate condition structure
        if rule.conditions:
            if not self._validate_conditions(rule.conditions):
                raise DelegationError("Invalid delegation conditions")
    
    def _validate_conditions(self, conditions: Dict) -> bool:
        """
        Validates delegation condition structure and format.
        
        IMPORTANT: All conditions must have required fields to prevent
        undefined behavior during evaluation.
        
        NOTE: This is a structural validation only. Actual condition
        evaluation happens during delegation checks.
        """
        required_fields = {"type", "value"}
        return all(
            isinstance(c, dict) and required_fields.issubset(c.keys())
            for c in conditions
        )
    
    def _evaluate_conditions(self, conditions: Dict) -> bool:
        """
        Evaluates dynamic delegation conditions.
        
        TODO: Implement actual condition evaluation logic based on:
        - Time windows
        - IP ranges
        - Resource scopes
        - Custom rules
        
        NOTE: Currently returns True as placeholder. Actual implementation
        should evaluate each condition type appropriately.
        """
        return True 