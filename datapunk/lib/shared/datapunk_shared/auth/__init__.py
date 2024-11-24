"""Authentication and Authorization System

This module provides a comprehensive security framework implementing industry-standard
authentication and authorization patterns for distributed systems.

ARCHITECTURE:
The system is organized into distinct components:
- Core: Fundamental types and utilities
- API Keys: Management and rotation of API credentials
- Policy: Access control and policy enforcement
- Audit: Compliance tracking and reporting

SECURITY CONSIDERATIONS:
- All components implement defense-in-depth principles
- Audit logging covers all security-critical operations
- Policy enforcement is consistent across distributed services

COMPLIANCE:
Supports common regulatory requirements including:
- SOC 2
- ISO 27001
- GDPR
- HIPAA
"""

from typing import TYPE_CHECKING

# Core types and utilities
# These form the foundation of the auth system and are used throughout
# all other components
from .core.types import (
    ResourceType, AccessLevel, AuthStatus,  # Basic auth primitives
    AccessContext, AccessResult,            # Access control types
    AuthContext, AuthResult,                # Auth flow types
    UserID, RoleID, ResourceID,            # Core identifiers
    TokenID, SessionID, RequestID,          # Request tracking
    ClientID, ValidationContext,            # Client context
    ValidationResult, Result, Metadata      # Operation results
)

# Type utilities for consistent data handling
from .core.type_utils import (
    TypeValidator,        # Input validation
    TypeConverter,        # Data transformation
    TypeSerializer,       # Serialization
    TypeValidationResult # Validation results
)

# Core auth components implementing the primary security functions
from .core.access_control import (
    AccessManager,    # Central access control
    AccessPolicy,     # Policy definitions
    ResourcePolicy    # Resource-specific rules
)

# Security configuration and middleware
from .core.middleware import AuthMiddleware  # Request authentication
from .core.config import (
    AuthConfig,          # Main configuration
    SecurityLevel,       # Security settings
    EncryptionLevel,     # Encryption options
    APIKeyConfig,        # API key settings
    PolicyConfig,        # Policy settings
    AuditConfig,         # Audit settings
    SecurityConfig,      # Security settings
    IntegrationConfig    # External integrations
)

# Error handling framework
from .core.error_handling import (
    ErrorHandler,        # Error processing
    ErrorSeverity,       # Error classification
    ErrorCategory,       # Error types
    ErrorContext,        # Error details
    ErrorThresholds,     # Alert thresholds
    ErrorReporter        # Error reporting
)

# API key management system
from .api_keys.manager import APIKeyManager  # Key lifecycle
from .api_keys.policies import (
    KeyType,                    # Key categories
    KeyPolicy,                  # Usage policies
    ComplianceRequirements,     # Compliance rules
    SecurityControls,           # Security measures
    ResourceQuota,              # Usage limits
    TimeWindow,                 # Time constraints
    CircuitBreaker              # Rate limiting
)

# Key rotation and validation
from .api_keys.rotation import (
    KeyRotationManager,  # Rotation handling
    RotationReason,      # Rotation triggers
    RotationConfig       # Rotation settings
)
from .api_keys.validation import (
    KeyValidator,         # Key validation
    KeyValidationConfig   # Validation rules
)

# Notification system for security events
from .api_keys.notifications import (
    KeyNotifier,           # Event notifications
    KeyEventType,          # Event types
    NotificationChannel,   # Delivery channels
    NotificationPriority,  # Alert priorities
    NotificationConfig     # Notification settings
)

# Policy management and enforcement
from .policy.types import (
    PolicyType,              # Policy categories
    PolicyStatus,            # Policy states
    RiskLevel,               # Risk assessment
    PolicyRule,              # Rule definitions
    Policy,                  # Policy container
    PolicyValidationResult,  # Validation results
    PolicyEvaluationResult   # Evaluation results
)

# Policy approval workflow
from .policy.approval.manager import (
    ApprovalManager,           # Approval handling
    ApprovalStatus,            # Approval states
    ApprovalLevel,             # Approval tiers
    ApprovalRequest,           # Request tracking
    ApprovalValidationConfig   # Validation rules
)

# Policy enforcement system
from .policy.enforcement.middleware import PolicyEnforcementMiddleware
from .policy.enforcement.rules import (
    RuleEngine,       # Rule processing
    RuleType,         # Rule categories
    EnforcementRule,  # Base rules
    TimeBasedRule,    # Time constraints
    RateLimitRule     # Rate limiting
)

# Policy rollback capabilities
from .policy.rollback.manager import (
    RollbackManager,  # Rollback handling
    RollbackPoint     # Rollback states
)

# Audit system for compliance
from .audit.types import (
    AuditLevel,           # Audit detail levels
    ComplianceStandard,   # Compliance frameworks
    AuditEvent,           # Audit records
    AuditContext,         # Audit context
    AuditResult           # Audit results
)

# Compliance tracking
from .audit.compliance.standards import (
    ComplianceStandards,      # Framework definitions
    ComplianceLevel,          # Compliance levels
    DataClassification,       # Data sensitivity
    SecurityControl,          # Security measures
    ComplianceRequirement     # Requirements
)

# Audit reporting system
from .audit.reporting.generator import (
    ReportGenerator,  # Report creation
    ReportFormat,     # Output formats
    ReportType,       # Report types
    ReportConfig      # Report settings
)

# Report templating system
from .audit.reporting.templates import (
    ReportTemplate,    # Template definitions
    TemplateType,      # Template categories
    ReportSection,     # Report structure
    TemplateConfig     # Template settings
)

# Template validation and caching
from .audit.reporting.template_validator import (
    TemplateValidator,         # Template validation
    TemplateValidationResult   # Validation results
)
from .audit.reporting.template_cache import (
    TemplateCache,          # Template caching
    TypeValidationResult    # Validation results
)

# Optional integrations with monitoring systems
if TYPE_CHECKING:
    from ..monitoring import MetricsClient
    from ..cache import CacheClient
    from ..messaging import MessageBroker

__version__ = "0.1.0"

# Public API surface
# These types and classes form the stable public interface
__all__ = [
    # Core types
    "ResourceType", "AccessLevel", "AuthStatus",
    "AccessContext", "AccessResult", "AuthContext", "AuthResult",
    "UserID", "RoleID", "ResourceID", "TokenID", "SessionID",
    "RequestID", "ClientID", "ValidationContext", "ValidationResult",
    "Result", "Metadata",
    
    # Type utilities
    "TypeValidator", "TypeConverter", "TypeSerializer",
    "TypeValidationResult",
    
    # Core components
    "AccessManager", "AccessPolicy", "ResourcePolicy",
    "AuthMiddleware", "AuthConfig", "SecurityLevel",
    "EncryptionLevel", "APIKeyConfig", "PolicyConfig",
    "AuditConfig", "SecurityConfig", "IntegrationConfig",
    "ErrorHandler", "ErrorSeverity", "ErrorCategory",
    "ErrorContext", "ErrorThresholds", "ErrorReporter",
    
    # API key components
    "APIKeyManager", "KeyType", "KeyPolicy",
    "ComplianceRequirements", "SecurityControls",
    "ResourceQuota", "TimeWindow", "CircuitBreaker",
    "KeyRotationManager", "RotationReason", "RotationConfig",
    "KeyValidator", "KeyValidationConfig", "KeyNotifier",
    "KeyEventType", "NotificationChannel", "NotificationPriority",
    "NotificationConfig",
    
    # Policy components
    "PolicyType", "PolicyStatus", "RiskLevel", "PolicyRule",
    "Policy", "PolicyValidationResult", "PolicyEvaluationResult",
    "ApprovalManager", "ApprovalStatus", "ApprovalLevel",
    "ApprovalRequest", "ApprovalValidationConfig",
    "PolicyEnforcementMiddleware", "RuleEngine", "RuleType",
    "EnforcementRule", "TimeBasedRule", "RateLimitRule",
    "RollbackManager", "RollbackPoint",
    
    # Audit components
    "AuditLevel", "ComplianceStandard", "AuditEvent",
    "AuditContext", "AuditResult", "ComplianceStandards",
    "ComplianceLevel", "DataClassification", "SecurityControl",
    "ComplianceRequirement", "ReportGenerator", "ReportFormat",
    "ReportType", "ReportConfig", "ReportTemplate",
    "TemplateType", "ReportSection", "TemplateConfig",
    "TemplateValidator", "TemplateValidationResult",
    "TemplateCache"
]
 