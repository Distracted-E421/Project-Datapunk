from datetime import datetime
from typing import Optional, Dict, Any
import structlog
from dataclasses import dataclass
from ..monitoring import MetricsClient

logger = structlog.get_logger()

@dataclass
class AuditEvent:
    """Audit event details."""
    event_type: str
    actor_id: str
    resource_type: str
    resource_id: str
    action: str
    timestamp: datetime
    status: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None

class AuditLogger:
    """Handles security audit logging."""
    
    def __init__(self, metrics: MetricsClient):
        self.logger = logger.bind(component="security_audit")
        self.metrics = metrics
    
    async def log_role_event(self,
                            event: AuditEvent) -> None:
        """Log role-related security event."""
        try:
            # Structure the log entry
            log_entry = {
                "event_type": event.event_type,
                "actor_id": event.actor_id,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "action": event.action,
                "timestamp": event.timestamp.isoformat(),
                "status": event.status
            }
            
            if event.details:
                log_entry["details"] = event.details
            if event.ip_address:
                log_entry["ip_address"] = event.ip_address
            if event.session_id:
                log_entry["session_id"] = event.session_id
            
            # Log the event
            self.logger.info("security_audit_event",
                           **log_entry)
            
            # Update metrics
            self.metrics.increment(
                "security_audit_events_total",
                tags={
                    "event_type": event.event_type,
                    "resource_type": event.resource_type,
                    "status": event.status
                }
            )
            
        except Exception as e:
            self.logger.error("audit_logging_failed",
                            error=str(e),
                            event=vars(event))
            raise 