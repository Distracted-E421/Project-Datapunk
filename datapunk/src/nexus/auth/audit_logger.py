from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
import json
import logging
import hashlib
import socket

class SecurityEventType(Enum):
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # Token events
    TOKEN_GENERATED = "token_generated"
    TOKEN_REFRESHED = "token_refreshed"
    TOKEN_REVOKED = "token_revoked"
    TOKEN_VALIDATION_FAILURE = "token_validation_failure"
    
    # Authorization events
    PERMISSION_DENIED = "permission_denied"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    POLICY_VIOLATION = "policy_violation"
    
    # Service auth events
    CERTIFICATE_ISSUED = "certificate_issued"
    CERTIFICATE_REVOKED = "certificate_revoked"
    SERVICE_REGISTERED = "service_registered"
    SERVICE_SUSPENDED = "service_suspended"
    
    # Security events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    CONFIGURATION_CHANGE = "configuration_change"

@dataclass
class SecurityEvent:
    timestamp: datetime
    event_type: SecurityEventType
    user_id: Optional[str]
    service_id: Optional[str]
    ip_address: str
    details: Dict[str, Any]
    event_id: str = ""
    
    def __post_init__(self):
        if not self.event_id:
            # Generate unique event ID
            data = f"{self.timestamp.isoformat()}:{self.event_type.value}:{self.user_id or ''}:{self.ip_address}"
            self.event_id = hashlib.sha256(data.encode()).hexdigest()[:32]
            
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "service_id": self.service_id,
            "ip_address": self.ip_address,
            "details": self.details
        }

class SecurityAuditLogger:
    def __init__(self, log_file: str, system_name: str = "nexus"):
        self.system_name = system_name
        self.hostname = socket.gethostname()
        
        # Configure file logger
        self.logger = logging.getLogger(f"{system_name}_security_audit")
        self.logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(log_file)
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)
        
    def log_event(self, event: SecurityEvent):
        """Log a security event."""
        event_data = event.to_dict()
        event_data["system"] = self.system_name
        event_data["hostname"] = self.hostname
        
        # Log as JSON for easy parsing
        self.logger.info(json.dumps(event_data))
        
        # Log critical events at warning level
        if self._is_critical_event(event.event_type):
            self.logger.warning(
                f"Critical security event: {event.event_type.value} - "
                f"User: {event.user_id}, IP: {event.ip_address}"
            )
            
    def _is_critical_event(self, event_type: SecurityEventType) -> bool:
        """Determine if an event type is critical."""
        critical_events = {
            SecurityEventType.LOGIN_FAILURE,
            SecurityEventType.PASSWORD_RESET,
            SecurityEventType.TOKEN_VALIDATION_FAILURE,
            SecurityEventType.PERMISSION_DENIED,
            SecurityEventType.POLICY_VIOLATION,
            SecurityEventType.CERTIFICATE_REVOKED,
            SecurityEventType.SERVICE_SUSPENDED,
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            SecurityEventType.CONFIGURATION_CHANGE
        }
        return event_type in critical_events
        
    def log_auth_event(self, event_type: SecurityEventType, user_id: str,
                      ip_address: str, **details):
        """Helper method to log authentication events."""
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            user_id=user_id,
            service_id=None,
            ip_address=ip_address,
            details=details
        )
        self.log_event(event)
        
    def log_service_event(self, event_type: SecurityEventType, service_id: str,
                         ip_address: str, **details):
        """Helper method to log service authentication events."""
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            user_id=None,
            service_id=service_id,
            ip_address=ip_address,
            details=details
        )
        self.log_event(event)
        
    def log_security_event(self, event_type: SecurityEventType, ip_address: str,
                          user_id: Optional[str] = None, service_id: Optional[str] = None,
                          **details):
        """Helper method to log general security events."""
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            user_id=user_id,
            service_id=service_id,
            ip_address=ip_address,
            details=details
        )
        self.log_event(event) 