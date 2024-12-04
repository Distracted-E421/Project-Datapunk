"""
Core type definitions for the security audit system.

This module defines the fundamental types used throughout the audit system,
supporting multiple compliance standards and configurable audit detail levels.

NOTE: When adding new fields to these types, ensure they align with relevant
compliance requirements (e.g., GDPR's data minimization principle).
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

class AuditLevel(Enum):
    """
    Defines granularity levels for audit logging to balance storage costs with compliance needs.
    
    IMPORTANT: Changing audit levels may impact compliance requirements. Ensure changes
    are reviewed against applicable standards.
    """
    MINIMAL = "minimal"     # Meets basic compliance requirements only
    STANDARD = "standard"   # Balanced detail for most use cases
    DETAILED = "detailed"   # Full audit trail for sensitive operations
    DEBUG = "debug"         # Temporary use during incident investigation

class ComplianceStandard(Enum):
    """
    Supported compliance frameworks for audit configuration.
    
    Each standard may require specific fields and retention periods.
    TODO: Add mapping of required fields per standard.
    """
    GDPR = "gdpr"           # Requires data minimization and explicit purpose
    HIPAA = "hipaa"         # Requires extended retention and access tracking
    SOX = "sox"             # Focuses on financial system access and changes
    PCI = "pci"             # Emphasizes cardholder data access
    ISO27001 = "iso27001"   # Broad security management requirements
    CCPA = "ccpa"           # California-specific privacy requirements
    NIST = "nist"           # U.S. government security standards
    SOC2 = "soc2"           # Service organization controls

@dataclass
class AuditEvent:
    """
    Comprehensive audit event structure supporting multiple compliance standards.
    
    This structure captures the WHO (user_id, client_ip), WHAT (action, resource_type),
    WHEN (timestamp), and HOW (changes, metadata) of security-relevant operations.
    
    NOTE: The optional fields allow for different detail levels while maintaining
    compatibility with various compliance requirements.
    """
    event_id: str           # Unique identifier for event correlation
    event_type: str         # Category of the event for filtering
    timestamp: datetime     # When the event occurred (always UTC)
    user_id: str           # Actor performing the action
    resource_id: str       # Target of the action
    resource_type: str     # Type of resource being accessed
    action: str            # Operation performed
    status: str            # Outcome of the action
    client_ip: Optional[str] = None      # Source IP, if available
    location: Optional[str] = None       # Geographic location for access patterns
    session_id: Optional[str] = None     # For session correlation
    request_id: Optional[str] = None     # For request tracing
    changes: Optional[Dict[str, Any]] = None    # Detailed change tracking
    metadata: Optional[Dict[str, Any]] = None   # Standard-specific requirements

@dataclass
class AuditContext:
    """
    Configuration context for audit processing.
    
    Defines how audit events should be processed, stored, and protected based on
    applicable compliance standards and organizational requirements.
    
    IMPORTANT: Changes to these settings may affect compliance status.
    TODO: Add validation for minimum requirements per compliance standard.
    """
    compliance_standards: List[ComplianceStandard]  # Active compliance frameworks
    audit_level: AuditLevel                         # Detail level for events
    retention_period: int  # Retention period in days
    require_encryption: bool = True    # Enforce at-rest encryption
    require_signing: bool = True      # Enable cryptographic signatures
    pii_detection: bool = True        # Scan for personal data
    metadata: Optional[Dict[str, Any]] = None  # Framework-specific settings

@dataclass
class AuditResult:
    """
    Outcome of audit event processing.
    
    Provides verification that audit events were properly processed, stored,
    and protected according to compliance requirements.
    
    NOTE: The signature field enables non-repudiation when required by
    compliance standards.
    """
    success: bool          # Whether processing succeeded
    event_id: str         # Reference to the original event
    timestamp: datetime   # When processing completed
    storage_location: str # Where the audit record is stored
    encryption_status: bool  # Confirms encryption if required
    signature: Optional[str] = None  # Cryptographic signature if enabled
    metadata: Optional[Dict[str, Any]] = None  # Processing details 