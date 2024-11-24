"""Core authentication and authorization components."""
from typing import TYPE_CHECKING

from .access_control import AccessManager, AccessPolicy, ResourcePolicy
from .middleware import AuthMiddleware
from .config import (
    AuthConfig, SecurityLevel, EncryptionLevel,
    APIKeyConfig, PolicyConfig, AuditConfig,
    SecurityConfig, IntegrationConfig
)
from .error_handling import (
    ErrorHandler, ErrorSeverity, ErrorCategory,
    ErrorContext, ErrorThresholds, ErrorReporter
)
from .types import (
    ResourceType, AccessLevel, AuthStatus,
    AccessContext, AccessResult, AuthContext, AuthResult
)
from .validation import ValidationContext, ValidationResult
from .exceptions import AuthError, ValidationError, ConfigError

if TYPE_CHECKING:
    from ...monitoring import MetricsClient
    from ...cache import CacheClient

__all__ = [
    # Access control
    "AccessManager", "AccessPolicy", "ResourcePolicy",
    
    # Middleware
    "AuthMiddleware",
    
    # Configuration
    "AuthConfig", "SecurityLevel", "EncryptionLevel",
    "APIKeyConfig", "PolicyConfig", "AuditConfig",
    "SecurityConfig", "IntegrationConfig",
    
    # Error handling
    "ErrorHandler", "ErrorSeverity", "ErrorCategory",
    "ErrorContext", "ErrorThresholds", "ErrorReporter",
    
    # Types
    "ResourceType", "AccessLevel", "AuthStatus",
    "AccessContext", "AccessResult", "AuthContext", "AuthResult",
    "ValidationContext", "ValidationResult",
    
    # Exceptions
    "AuthError", "ValidationError", "ConfigError"
] 