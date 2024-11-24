"""Type definitions for audit system."""
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

class AuditLevel(Enum):
    """Audit detail levels."""
    MINIMAL = "minimal"     # Basic event info only
    STANDARD = "standard"   # Standard detail level
    DETAILED = "detailed"   # Full event details
    DEBUG = "debug"        # Debug-level details

class ComplianceStandard(Enum):
    """Supported compliance standards."""
    GDPR = "gdpr"           # EU data protection
    HIPAA = "hipaa"         # Healthcare privacy
    SOX = "sox"             # Financial controls
    PCI = "pci"             # Payment card security
    ISO27001 = "iso27001"   # Security management
    CCPA = "ccpa"           # California privacy
    NIST = "nist"           # US government
    SOC2 = "soc2"           # Service organization

@dataclass
class AuditEvent:
    """Audit event structure."""
    event_id: str
    event_type: str
    timestamp: datetime
    user_id: str
    resource_id: str
    resource_type: str
    action: str
    status: str
    client_ip: Optional[str] = None
    location: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AuditContext:
    """Context for audit events."""
    compliance_standards: List[ComplianceStandard]
    audit_level: AuditLevel
    retention_period: int  # days
    require_encryption: bool = True
    require_signing: bool = True
    pii_detection: bool = True
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AuditResult:
    """Result of audit processing."""
    success: bool
    event_id: str
    timestamp: datetime
    storage_location: str
    encryption_status: bool
    signature: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None 