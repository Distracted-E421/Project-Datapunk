"""Core authentication and authorization components.

This module provides a comprehensive authentication and authorization framework
for the Datapunk application. It implements a layered security approach with:
- Role-based access control (RBAC)
- Policy-based authorization
- Configurable security levels
- Audit logging and error handling

The components are designed to be extensible and can integrate with various
authentication providers and security protocols.

NOTE: This module requires the monitoring and cache clients to be properly
configured before use.
"""
from typing import TYPE_CHECKING

# Core access control components for implementing RBAC and policy enforcement
from .access_control import AccessManager, AccessPolicy, ResourcePolicy

# Request pipeline integration for authentication/authorization checks
from .middleware import AuthMiddleware

# Security configuration components with different protection levels
from .config import (
    AuthConfig, SecurityLevel, EncryptionLevel,  # Base security settings
    APIKeyConfig, PolicyConfig, AuditConfig,     # Feature-specific configs
    SecurityConfig, IntegrationConfig            # Integration settings
)

# Comprehensive error handling system with severity levels and reporting
from .error_handling import (
    ErrorHandler, ErrorSeverity, ErrorCategory,
    ErrorContext, ErrorThresholds, ErrorReporter
)

# Type definitions for authentication and authorization operations
from .types import (
    ResourceType, AccessLevel, AuthStatus,      # Core type definitions
    AccessContext, AccessResult,                # Access control results
    AuthContext, AuthResult                     # Authentication results
)

# Input validation components
from .validation import ValidationContext, ValidationResult

# Custom exceptions for different security-related errors
from .exceptions import AuthError, ValidationError, ConfigError

# Optional dependencies that enhance functionality when available
if TYPE_CHECKING:
    from ...monitoring import MetricsClient    # For security metrics tracking
    from ...cache import CacheClient          # For caching auth decisions

# Public API exports
# TODO: Consider grouping exports by functionality using dictionaries
__all__ = [
    # Access control components for implementing security policies
    "AccessManager", "AccessPolicy", "ResourcePolicy",
    
    # Authentication middleware for request processing
    "AuthMiddleware",
    
    # Configuration classes for different security aspects
    "AuthConfig", "SecurityLevel", "EncryptionLevel",
    "APIKeyConfig", "PolicyConfig", "AuditConfig",
    "SecurityConfig", "IntegrationConfig",
    
    # Error handling system components
    "ErrorHandler", "ErrorSeverity", "ErrorCategory",
    "ErrorContext", "ErrorThresholds", "ErrorReporter",
    
    # Type definitions for type safety and documentation
    "ResourceType", "AccessLevel", "AuthStatus",
    "AccessContext", "AccessResult", "AuthContext", "AuthResult",
    "ValidationContext", "ValidationResult",
    
    # Security-related exceptions
    "AuthError", "ValidationError", "ConfigError"
] 