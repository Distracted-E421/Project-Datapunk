"""
Delegation Audit System

Provides comprehensive audit trails for authority delegation operations within
the security framework. Designed to meet SOC2, ISO 27001, and GDPR requirements
for access control monitoring and accountability.

Key features:
- Immutable audit records for all delegation lifecycle events
- Real-time metrics for security monitoring
- Correlation data for security incident investigation
- Compliance evidence gathering

NOTE: All timestamps are in UTC to ensure consistent audit trails across timezones
and distributed systems.
"""

from typing import Dict, Optional
import structlog
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from .approval_delegation import DelegationType, DelegationRule
from ..monitoring import MetricsClient

logger = structlog.get_logger()

class DelegationAction(Enum):
    """
    Auditable events in delegation lifecycle.
    
    Designed to track:
    - Authority establishment and termination (CREATE, REVOKE)
    - Actual authority exercise (USE)
    - Automated state changes (EXPIRE)
    - Policy enforcement (VALIDATE)
    - Configuration changes (MODIFY)
    
    NOTE: Each action type has specific required context fields
    defined in DelegationAuditEvent.
    """
    CREATE = "create"
    REVOKE = "revoke"
    USE = "use"
    EXPIRE = "expire"
    MODIFY = "modify"
    VALIDATE = "validate"

@dataclass
class DelegationAuditEvent:
    """
    Structured audit record format ensuring consistent logging across all
    delegation operations.
    
    Required fields capture:
    - Who: delegator_id, delegate_id
    - What: action, delegation_type, level
    - When: timestamp
    - Result: success
    
    Optional context adds:
    - Why: reason, metadata
    - Where: ip_address
    - Session: session_id
    
    IMPORTANT: Optional fields should be included whenever available to
    support security investigation and access pattern analysis.
    """
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
    """
    Central component for delegation audit logging, integrating with enterprise
    logging infrastructure for compliance and security monitoring.
    
    Architecture:
    - Audit logger: Tamper-evident, long-term storage
    - Metrics client: Real-time monitoring and alerting
    - Application logger: Operational debugging
    
    IMPORTANT: Audit logging failures are logged but don't block operations
    to prevent disruption of critical security functions.
    
    NOTE: Consider implementing retry logic for failed audit writes in
    high-compliance environments.
    
    TODO: Add support for bulk logging operations to improve performance
    during mass delegation changes.
    """
    
    def __init__(self,
                 audit_logger,
                 metrics: MetricsClient):
        """
        Initialize auditor with required logging infrastructure.
        
        IMPORTANT: audit_logger must support:
        - Immutable storage
        - Long-term retention
        - Structured data logging
        - High-availability writes
        """
        self.audit = audit_logger
        self.metrics = metrics
        self.logger = logger.bind(component="delegation_audit")
    
    async def log_delegation_event(self,
                                 event: DelegationAuditEvent) -> bool:
        """
        Records delegation events across multiple logging channels for different purposes:
        - Audit log: Immutable, long-term compliance record
        - Metrics: Real-time monitoring and alerting
        - Application log: Operational debugging
        
        NOTE: All timestamps are in UTC to ensure consistent audit trails
        across distributed systems.
        """
        try:
            # Structured format ensures consistent parsing for audit tools
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
            
            # Severity reflects success/failure for incident detection
            await self.audit.log_event(
                "delegation_audit",
                audit_entry,
                severity="INFO" if event.success else "WARNING"
            )
            
            # Metrics tagged for multi-dimensional analysis
            self.metrics.increment(
                "delegation_operations_total",
                {
                    "action": event.action.value,
                    "type": event.delegation_type.value,
                    "success": str(event.success).lower()
                }
            )
            
            # Operational logs include context for troubleshooting
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
            # Log but don't fail operations on audit errors
            self.logger.error("audit_logging_failed", error=str(e))
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
        """
        Records delegation revocation events.
        
        IMPORTANT: Type defaults to TEMPORARY as historical type may be unavailable
        during revocation. Level is marked unknown as it's not relevant for revocation
        tracking.
        
        NOTE: IP and session tracking particularly important for revocations
        to detect potential security incidents.
        """
        await self.log_delegation_event(
            DelegationAuditEvent(
                timestamp=datetime.utcnow(),
                action=DelegationAction.REVOKE,
                delegator_id=delegator_id,
                delegate_id=delegate_id,
                delegation_type=DelegationType.TEMPORARY,
                level="unknown",
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
        """
        Tracks actual usage of delegated authority.
        
        IMPORTANT: Usage tracking is critical for:
        - Detecting delegation abuse
        - Identifying unused delegations
        - Supporting access reviews
        
        NOTE: Type defaults to TEMPORARY as it's most common and
        type-specific tracking isn't required for usage patterns.
        """
        await self.log_delegation_event(
            DelegationAuditEvent(
                timestamp=datetime.utcnow(),
                action=DelegationAction.USE,
                delegator_id=delegator_id,
                delegate_id=delegate_id,
                delegation_type=DelegationType.TEMPORARY,
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
        """
        Records automatic delegation expiration.
        
        NOTE: IP/session tracking omitted as this is a system-triggered event.
        Expiration success is always True as it's a state transition rather
        than an operation that can fail.
        """
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
        """
        Tracks delegation validation checks.
        
        IMPORTANT: Validation logging helps identify:
        - Attempted abuse of expired delegations
        - Configuration issues preventing valid delegation use
        - Patterns requiring delegation policy updates
        
        NOTE: IP/session tracking omitted as validations may occur
        in multiple contexts (user requests, system checks, etc).
        """
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