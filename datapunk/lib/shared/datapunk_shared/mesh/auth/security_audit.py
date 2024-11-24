from typing import Dict, Any, Optional
import json
import time
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from prometheus_client import Counter, Histogram

class AuditEventType(Enum):
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    ACCESS_DENIED = "access_denied"
    ACCESS_GRANTED = "access_granted"
    CONFIG_CHANGE = "config_change"
    CERT_ROTATION = "cert_rotation"
    KEY_ROTATION = "key_rotation"
    POLICY_CHANGE = "policy_change"
    RATE_LIMIT_BREACH = "rate_limit_breach"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

@dataclass
class AuditEvent:
    event_type: AuditEventType
    service_id: str
    timestamp: float
    details: Dict[str, Any]
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    severity: str = "INFO"

class SecurityAuditor:
    def __init__(self, log_path: str = "security_audit.log"):
        self.logger = logging.getLogger("security_audit")
        self.file_handler = logging.FileHandler(log_path)
        self.file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(self.file_handler)
        self.logger.setLevel(logging.INFO)
        
        # Metrics
        self.audit_events = Counter(
            'security_audit_events_total',
            'Total number of security audit events',
            ['event_type', 'service_id', 'severity']
        )
        self.event_processing_time = Histogram(
            'security_audit_processing_seconds',
            'Time spent processing security audit events',
            ['event_type']
        )

    async def log_event(self, event: AuditEvent) -> None:
        """Log a security audit event"""
        start_time = time.time()
        try:
            # Format event for logging
            log_entry = {
                "timestamp": datetime.fromtimestamp(event.timestamp).isoformat(),
                "event_type": event.event_type.value,
                "service_id": event.service_id,
                "details": event.details,
                "source_ip": event.source_ip,
                "user_agent": event.user_agent,
                "request_id": event.request_id,
                "severity": event.severity
            }

            # Write to log file
            self.logger.log(
                logging.getLevelName(event.severity),
                json.dumps(log_entry)
            )

            # Update metrics
            self.audit_events.labels(
                event_type=event.event_type.value,
                service_id=event.service_id,
                severity=event.severity
            ).inc()

        except Exception as e:
            self.logger.error(f"Failed to log audit event: {str(e)}")
        finally:
            # Record processing time
            self.event_processing_time.labels(
                event_type=event.event_type.value
            ).observe(time.time() - start_time)

    async def query_events(
        self,
        service_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Query audit events with filters"""
        # Implementation would depend on your storage backend
        # This is a placeholder for the interface
        pass 