"""
Authentication and authorization system.

This module provides comprehensive auth functionality including:
- API key management
- Policy enforcement
- Access control
- Audit logging
- Compliance tracking
"""

from typing import TYPE_CHECKING

# Core types and utilities
from .core.types import (
    ResourceType, AccessLevel, AuthStatus,
    AccessContext, AccessResult, AuthContext, AuthResult,
    UserID, RoleID, ResourceID, TokenID, SessionID, RequestID, ClientID,
    ValidationContext, ValidationResult, Result, Metadata
)
from .core.type_utils import (
    TypeValidator, TypeConverter, TypeSerializer,
    TypeValidationResult
)

# Core auth components
from .core.access_control import (
    AccessManager,
    AccessPolicy,
    ResourcePolicy
)
from .core.middleware import AuthMiddleware
from .core.config import (
    AuthConfig,
    SecurityLevel,
    EncryptionLevel,
    APIKeyConfig,
    PolicyConfig,
    AuditConfig,
    SecurityConfig,
    IntegrationConfig
)
from .core.error_handling import (
    ErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    ErrorThresholds,
    ErrorReporter
)

# API key components
from .api_keys.manager import APIKeyManager
from .api_keys.policies import (
    KeyType,
    KeyPolicy,
    ComplianceRequirements,
    SecurityControls,
    ResourceQuota,
    TimeWindow,
    CircuitBreaker
)
from .api_keys.rotation import (
    KeyRotationManager,
    RotationReason,
    RotationConfig
)
from .api_keys.validation import (
    KeyValidator,
    KeyValidationConfig
)
from .api_keys.notifications import (
    KeyNotifier,
    KeyEventType,
    NotificationChannel,
    NotificationPriority,
    NotificationConfig
)

# Policy components
from .policy.types import (
    PolicyType,
    PolicyStatus,
    RiskLevel,
    PolicyRule,
    Policy,
    PolicyValidationResult,
    PolicyEvaluationResult
)
from .policy.approval.manager import (
    ApprovalManager,
    ApprovalStatus,
    ApprovalLevel,
    ApprovalRequest,
    ApprovalValidationConfig
)
from .policy.enforcement.middleware import PolicyEnforcementMiddleware
from .policy.enforcement.rules import (
    RuleEngine,
    RuleType,
    EnforcementRule,
    TimeBasedRule,
    RateLimitRule
)
from .policy.rollback.manager import (
    RollbackManager,
    RollbackPoint
)

# Audit components
from .audit.types import (
    AuditLevel,
    ComplianceStandard,
    AuditEvent,
    AuditContext,
    AuditResult
)
from .audit.compliance.standards import (
    ComplianceStandards,
    ComplianceLevel,
    DataClassification,
    SecurityControl,
    ComplianceRequirement
)
from .audit.reporting.generator import (
    ReportGenerator,
    ReportFormat,
    ReportType,
    ReportConfig
)
from .audit.reporting.templates import (
    ReportTemplate,
    TemplateType,
    ReportSection,
    TemplateConfig
)
from .audit.reporting.template_validator import (
    TemplateValidator,
    TemplateValidationResult
)
from .audit.reporting.template_cache import (
    TemplateCache,
    TypeValidationResult
)

if TYPE_CHECKING:
    from ..monitoring import MetricsClient
    from ..cache import CacheClient
    from ..messaging import MessageBroker

__version__ = "0.1.0"

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
 