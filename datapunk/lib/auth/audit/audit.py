from datetime import datetime
from typing import Optional, Dict, Any
import structlog
from dataclasses import dataclass
from ..monitoring import MetricsClient

# Configure structured logger for consistent log formatting
logger = structlog.get_logger()

@dataclass
class AuditEvent:
    """
    Represents a security audit event with standardized fields for compliance and tracking.
    
    This class follows security logging best practices by capturing:
    - Who: actor_id, ip_address, session_id
    - What: event_type, action, resource_type, resource_id
    - When: timestamp
    - Result: status, details
    
    NOTE: All sensitive data should be sanitized before being included in the details field
    """
    event_type: str    # Category of the security event (e.g., 'role_change', 'access_attempt')
    actor_id: str      # Identifier of the user/system performing the action
    resource_type: str # Type of resource being accessed/modified
    resource_id: str   # Identifier of the specific resource
    action: str        # Specific operation performed (e.g., 'create', 'modify', 'delete')
    timestamp: datetime
    status: str        # Outcome of the action (e.g., 'success', 'failure')
    details: Optional[Dict[str, Any]] = None  # Additional context-specific information
    ip_address: Optional[str] = None          # Source IP address of the request
    session_id: Optional[str] = None          # Session identifier for request correlation

class AuditLogger:
    """
    Handles security audit logging with integrated metrics tracking.
    
    This class provides a centralized way to log security-relevant events
    while maintaining consistent formatting and ensuring proper metric collection.
    
    IMPORTANT: This logger should be used for all security-relevant operations
    to maintain compliance with security auditing requirements.
    
    TODO: Add support for log encryption and external audit log shipping
    """
    
    def __init__(self, metrics: MetricsClient):
        # Bind component name for easier log filtering and aggregation
        self.logger = logger.bind(component="security_audit")
        self.metrics = metrics
    
    async def log_role_event(self, event: AuditEvent) -> None:
        """
        Log role-related security events with associated metrics.
        
        This method ensures consistent logging of role management operations
        while updating relevant security metrics for monitoring and alerting.
        
        NOTE: This method will raise exceptions on logging failures to ensure
        security events are never silently dropped.
        
        Args:
            event: AuditEvent containing all relevant security event details
            
        Raises:
            Exception: If logging or metrics collection fails
        """
        try:
            # Structure the log entry with mandatory fields first
            log_entry = {
                "event_type": event.event_type,
                "actor_id": event.actor_id,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "action": event.action,
                "timestamp": event.timestamp.isoformat(),
                "status": event.status
            }
            
            # Add optional fields only if present to keep logs clean
            if event.details:
                log_entry["details"] = event.details
            if event.ip_address:
                log_entry["ip_address"] = event.ip_address
            if event.session_id:
                log_entry["session_id"] = event.session_id
            
            # Log the event using structured logging for better searchability
            self.logger.info("security_audit_event", **log_entry)
            
            # Track security events metrics for monitoring and alerting
            self.metrics.increment(
                "security_audit_events_total",
                tags={
                    "event_type": event.event_type,
                    "resource_type": event.resource_type,
                    "status": event.status
                }
            )
            
        except Exception as e:
            # Log the error with full context before re-raising
            self.logger.error("audit_logging_failed",
                            error=str(e),
                            event=vars(event))
            # Re-raise to ensure calling code knows logging failed
            raise 