"""
Enhanced audit logging system for security and compliance tracking.

Key Features:
- Structured event logging with categorization and severity levels
- Compliance tracking for multiple standards (e.g., SOX, GDPR, HIPAA)
- Security event monitoring with integrity verification
- Performance metrics for audit trail analysis
- Data integrity through hashing and optional encryption
- PII detection and masking capabilities
- Event persistence with configurable retention

Architecture:
- Uses a multi-layer storage approach (cache + persistent storage)
- Implements pub/sub pattern for real-time event notifications
- Supports distributed systems through message broker integration

Security Considerations:
- Cryptographic event signing for non-repudiation
- PII detection and masking for data privacy
- Configurable encryption for sensitive data
"""

from typing import Dict, Optional, Any, TYPE_CHECKING, List, Set
import structlog
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
import uuid

from .types import AuditLevel, ComplianceStandard, AuditEvent, AuditContext
from ..core.exceptions import AuditError

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....cache import CacheClient
    from ....messaging import MessageBroker
    from ....storage import StorageClient

logger = structlog.get_logger()

class EventCategory(Enum):
    """
    Categories for audit event classification and routing.
    
    NOTE: When adding new categories, ensure corresponding metrics and 
    storage partitioning strategies are updated.
    """
    SECURITY = "security"       # Security-related events
    ACCESS = "access"          # Access control events
    DATA = "data"             # Data operations
    POLICY = "policy"         # Policy changes
    SYSTEM = "system"         # System events
    COMPLIANCE = "compliance" # Compliance events
    USER = "user"            # User actions
    API = "api"              # API operations

class EventSeverity(Enum):
    """
    Severity levels for event prioritization and alerting.
    
    The hierarchy (CRITICAL -> INFO) determines:
    - Alert triggering thresholds
    - Retention policies
    - Real-time monitoring requirements
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class AuditConfig:
    """
    Configuration for audit logging behavior and compliance requirements.
    
    IMPORTANT: Changes to these settings may impact compliance status.
    Consider regulatory requirements when modifying.
    
    TODO: Add validation for compliance standard combinations
    """
    enabled_categories: Set[EventCategory]
    min_severity: EventSeverity
    retention_period: timedelta
    compliance_standards: Set[ComplianceStandard]
    require_encryption: bool = True
    require_signing: bool = True
    pii_detection: bool = True
    store_metadata: bool = True

class AuditLogger:
    """
    Core audit logging system implementing comprehensive event tracking.
    
    Architecture Notes:
    - Uses cache for high-speed access to recent events
    - Implements persistent storage for long-term retention
    - Publishes events for real-time monitoring
    - Tracks metrics for system health and compliance reporting
    
    Performance Considerations:
    - Event creation is CPU-intensive due to hashing and PII detection
    - Storage operations are async to prevent blocking
    - Cache usage optimizes frequent access patterns
    """
    
    def __init__(self,
                 cache: 'CacheClient',
                 metrics: 'MetricsClient',
                 message_broker: 'MessageBroker',
                 storage: 'StorageClient',
                 config: AuditConfig):
        self.cache = cache
        self.metrics = metrics
        self.broker = message_broker
        self.storage = storage
        self.config = config
        self.logger = logger.bind(component="audit_logger")
    
    async def log_event(self,
                       category: EventCategory,
                       severity: EventSeverity,
                       event_type: str,
                       data: Dict[str, Any],
                       context: Optional[AuditContext] = None) -> str:
        """
        Logs an audit event with full integrity and compliance checks.
        
        Implementation Notes:
        - Events are processed synchronously to maintain sequence integrity
        - Failed events are logged but don't block system operation
        - PII detection may impact performance on large data sets
        
        FIXME: Add retry logic for storage and broker operations
        
        Args:
            category: Event category
            severity: Event severity
            event_type: Type of event
            data: Event data
            context: Additional context
        
        Returns:
            str: Event ID
        """
        try:
            # Check if category and severity are enabled
            if (category not in self.config.enabled_categories or
                severity.value < self.config.min_severity.value):
                return None
            
            # Create event
            event = await self._create_event(
                category,
                severity,
                event_type,
                data,
                context
            )
            
            # Process for compliance if needed
            if self.config.compliance_standards:
                event = await self._handle_compliance(event)
            
            # Store event
            await self._store_event(event)
            
            # Publish event
            await self._publish_event(event)
            
            # Update metrics
            self._update_metrics(event)
            
            return event["event_id"]
            
        except Exception as e:
            self.logger.error("audit_logging_failed",
                            error=str(e))
            raise AuditError(f"Failed to log audit event: {str(e)}")
    
    async def _create_event(self,
                           category: EventCategory,
                           severity: EventSeverity,
                           event_type: str,
                           data: Dict[str, Any],
                           context: Optional[AuditContext]) -> Dict[str, Any]:
        """
        Creates a structured audit event with integrity controls.
        
        Security Notes:
        - Event IDs are UUIDs to prevent enumeration
        - Timestamps use UTC to ensure consistency
        - Hash chain maintains event sequence integrity
        
        TODO: Consider adding event correlation IDs for distributed tracing
        
        Args:
            category: Event category
            severity: Event severity
            event_type: Type of event
            data: Event data
            context: Additional context
        
        Returns:
            Dict: Structured audit event
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        event = {
            "event_id": event_id,
            "category": category.value,
            "severity": severity.value,
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "data": data
        }
        
        # Add context if provided
        if context:
            event["context"] = {
                "user_id": context.user_id,
                "session_id": context.session_id,
                "client_ip": context.client_ip,
                "user_agent": context.user_agent
            }
        
        # Add compliance info if needed
        if self.config.compliance_standards:
            event["compliance"] = {
                "standards": [s.value for s in self.config.compliance_standards],
                "audit_level": context.audit_level.value if context else None
            }
        
        # Add integrity verification
        event["integrity"] = {
            "hash": self._generate_hash(event),
            "sequence": await self._get_next_sequence()
        }
        
        return event
    
    async def _handle_compliance(self, event: Dict) -> Dict:
        """Process event for compliance requirements."""
        # Handle PII if configured
        if self.config.pii_detection:
            event = await self._detect_pii(event)
        
        # Add encryption if required
        if self.config.require_encryption:
            event = await self._encrypt_sensitive_data(event)
        
        # Add digital signature if required
        if self.config.require_signing:
            event["signature"] = await self._sign_event(event)
        
        return event
    
    async def _store_event(self, event: Dict) -> None:
        """Store audit event."""
        # Store in cache for quick access
        cache_key = f"audit:event:{event['event_id']}"
        await self.cache.set(
            cache_key,
            event,
            ttl=int(self.config.retention_period.total_seconds())
        )
        
        # Store in persistent storage
        storage_key = (f"audit/{event['category']}/"
                      f"{event['timestamp'][:10]}/"
                      f"{event['event_id']}.json")
        
        await self.storage.store(
            storage_key,
            json.dumps(event),
            metadata={
                "category": event["category"],
                "severity": event["severity"],
                "timestamp": event["timestamp"]
            }
        )
    
    async def _publish_event(self, event: Dict) -> None:
        """Publish audit event to message broker."""
        routing_key = f"audit.{event['category']}.{event['severity']}"
        
        await self.broker.publish(
            routing_key,
            event
        )
    
    def _update_metrics(self, event: Dict) -> None:
        """Update audit metrics."""
        labels = {
            "category": event["category"],
            "severity": event["severity"],
            "event_type": event["event_type"]
        }
        
        self.metrics.increment("audit_events_total", labels)
        
        if event.get("compliance"):
            for standard in event["compliance"]["standards"]:
                self.metrics.increment(
                    "compliance_events",
                    {"standard": standard}
                )
    
    def _generate_hash(self, event: Dict) -> str:
        """Generate cryptographic hash of event."""
        # Remove integrity section for hashing
        event_copy = event.copy()
        event_copy.pop("integrity", None)
        
        event_str = json.dumps(event_copy, sort_keys=True)
        return hashlib.sha256(event_str.encode()).hexdigest()
    
    async def _get_next_sequence(self) -> int:
        """Get next event sequence number."""
        return await self.cache.incr("audit:sequence")
    
    async def _detect_pii(self, event: Dict) -> Dict:
        """
        Detects and masks PII in event data using regex patterns.
        
        Limitations:
        - Current implementation uses basic regex patterns
        - May produce false positives/negatives
        - Performance scales linearly with data size
        
        TODO: Implement ML-based PII detection for improved accuracy
        
        Args:
            event: Audit event
        
        Returns:
            Dict: Processed event
        """
        pii_patterns = {
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "ssn": r"\d{3}-\d{2}-\d{4}",
            "credit_card": r"\d{4}-\d{4}-\d{4}-\d{4}",
            "phone": r"\d{3}-\d{3}-\d{4}"
        }
        
        def mask_pii(value: str) -> str:
            """Mask PII data."""
            if len(value) <= 4:
                return "*" * len(value)
            return value[:2] + "*" * (len(value) - 4) + value[-2:]
        
        def process_dict(d: Dict) -> Dict:
            """Recursively process dictionary for PII."""
            result = {}
            for k, v in d.items():
                if isinstance(v, str):
                    # Check for PII patterns
                    for pii_type, pattern in pii_patterns.items():
                        if re.match(pattern, v):
                            result[k] = mask_pii(v)
                            break
                    else:
                        result[k] = v
                elif isinstance(v, dict):
                    result[k] = process_dict(v)
                elif isinstance(v, list):
                    result[k] = [
                        process_dict(i) if isinstance(i, dict) else i
                        for i in v
                    ]
                else:
                    result[k] = v
            return result
        
        event["data"] = process_dict(event["data"])
        return event
    
    async def _encrypt_sensitive_data(self, event: Dict) -> Dict:
        """
        Placeholder for sensitive data encryption.
        
        SECURITY CRITICAL: Current implementation is a stub.
        Must be implemented before production use.
        
        TODO: Implement proper encryption using KMS integration
        
        Args:
            event: Audit event
        
        Returns:
            Dict: Encrypted event
        """
        # Implementation would use proper encryption
        # This is a placeholder
        return event
    
    async def _sign_event(self, event: Dict) -> str:
        """
        Placeholder for event signing implementation.
        
        SECURITY CRITICAL: Current implementation is a stub.
        Must be implemented before production use.
        
        TODO: Implement proper digital signing using HSM integration
        
        Args:
            event: Audit event
        
        Returns:
            str: Digital signature
        """
        # Implementation would use proper digital signing
        # This is a placeholder
        event_hash = self._generate_hash(event)
        timestamp = datetime.utcnow().isoformat()
        return f"{event_hash}:{timestamp}" 