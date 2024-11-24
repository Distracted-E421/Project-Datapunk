from typing import Dict, Optional
import structlog
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from .approval_delegation import DelegationType, DelegationRule
from ..monitoring import MetricsClient

logger = structlog.get_logger()

class DelegationAction(Enum):
    """Types of delegation actions to audit."""
    CREATE = "create"
    REVOKE = "revoke"
    USE = "use"
    EXPIRE = "expire"
    MODIFY = "modify"
    VALIDATE = "validate"

@dataclass
class DelegationAuditEvent:
    """Audit event for delegation operations."""
    timestamp: datetime
    action: DelegationAction
    delegator_id: str
    delegate_id: str
    delegation_type: DelegationType
    level: str
    success: bool
    reason: Optional[str] = None
    metadata: Optional[Dict] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None

class DelegationAuditor:
    """Handles audit logging for delegation operations."""
    
    def __init__(self,
                 audit_logger,
                 metrics: MetricsClient):
        self.audit = audit_logger
        self.metrics = metrics
        self.logger = logger.bind(component="delegation_audit")
    
    async def log_delegation_event(self,
                                 event: DelegationAuditEvent) -> bool:
        """Log delegation audit event."""
        try:
            # Format audit log entry
            audit_entry = {
                "timestamp": event.timestamp.isoformat(),
                "action": event.action.value,
                "delegator_id": event.delegator_id,
                "delegate_id": event.delegate_id,
                "delegation_type": event.delegation_type.value,
                "level": event.level,
                "success": event.success,
                "reason": event.reason,
                "metadata": event.metadata,
                "ip_address": event.ip_address,
                "session_id": event.session_id
            }
            
            # Write to audit log
            await self.audit.log_event(
                "delegation_audit",
                audit_entry,
                severity="INFO" if event.success else "WARNING"
            )
            
            # Update metrics
            self.metrics.increment(
                "delegation_operations_total",
                {
                    "action": event.action.value,
                    "type": event.delegation_type.value,
                    "success": str(event.success).lower()
                }
            )
            
            # Log for observability
            log_level = "info" if event.success else "warning"
            getattr(self.logger, log_level)(
                "delegation_operation",
                action=event.action.value,
                delegator=event.delegator_id,
                delegate=event.delegate_id,
                success=event.success,
                reason=event.reason
            )
            
            return True
            
        except Exception as e:
            self.logger.error("audit_logging_failed",
                            error=str(e))
            return False
    
    async def log_creation(self,
                          rule: DelegationRule,
                          success: bool,
                          reason: Optional[str] = None,
                          metadata: Optional[Dict] = None,
                          ip_address: Optional[str] = None,
                          session_id: Optional[str] = None) -> None:
        """Audit delegation creation."""
        await self.log_delegation_event(
            DelegationAuditEvent(
                timestamp=datetime.utcnow(),
                action=DelegationAction.CREATE,
                delegator_id=rule.delegator_id,
                delegate_id=rule.delegate_id,
                delegation_type=rule.type,
                level=rule.level.value,
                success=success,
                reason=reason,
                metadata=metadata,
                ip_address=ip_address,
                session_id=session_id
            )
        )
    
    async def log_revocation(self,
                            delegator_id: str,
                            delegate_id: str,
                            success: bool,
                            reason: Optional[str] = None,
                            metadata: Optional[Dict] = None,
                            ip_address: Optional[str] = None,
                            session_id: Optional[str] = None) -> None:
        """Audit delegation revocation."""
        await self.log_delegation_event(
            DelegationAuditEvent(
                timestamp=datetime.utcnow(),
                action=DelegationAction.REVOKE,
                delegator_id=delegator_id,
                delegate_id=delegate_id,
                delegation_type=DelegationType.TEMPORARY,  # Default type for revocation
                level="unknown",  # Level may not be available during revocation
                success=success,
                reason=reason,
                metadata=metadata,
                ip_address=ip_address,
                session_id=session_id
            )
        )
    
    async def log_usage(self,
                       delegator_id: str,
                       delegate_id: str,
                       level: str,
                       success: bool,
                       reason: Optional[str] = None,
                       metadata: Optional[Dict] = None,
                       ip_address: Optional[str] = None,
                       session_id: Optional[str] = None) -> None:
        """Audit delegation usage."""
        await self.log_delegation_event(
            DelegationAuditEvent(
                timestamp=datetime.utcnow(),
                action=DelegationAction.USE,
                delegator_id=delegator_id,
                delegate_id=delegate_id,
                delegation_type=DelegationType.TEMPORARY,  # Default type for usage
                level=level,
                success=success,
                reason=reason,
                metadata=metadata,
                ip_address=ip_address,
                session_id=session_id
            )
        )
    
    async def log_expiration(self,
                           rule: DelegationRule,
                           reason: Optional[str] = None,
                           metadata: Optional[Dict] = None) -> None:
        """Audit delegation expiration."""
        await self.log_delegation_event(
            DelegationAuditEvent(
                timestamp=datetime.utcnow(),
                action=DelegationAction.EXPIRE,
                delegator_id=rule.delegator_id,
                delegate_id=rule.delegate_id,
                delegation_type=rule.type,
                level=rule.level.value,
                success=True,
                reason=reason,
                metadata=metadata
            )
        )
    
    async def log_validation(self,
                           rule: DelegationRule,
                           success: bool,
                           reason: Optional[str] = None,
                           metadata: Optional[Dict] = None) -> None:
        """Audit delegation validation."""
        await self.log_delegation_event(
            DelegationAuditEvent(
                timestamp=datetime.utcnow(),
                action=DelegationAction.VALIDATE,
                delegator_id=rule.delegator_id,
                delegate_id=rule.delegate_id,
                delegation_type=rule.type,
                level=rule.level.value,
                success=success,
                reason=reason,
                metadata=metadata
            )
        ) 