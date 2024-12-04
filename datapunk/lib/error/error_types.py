"""
Error Type Definitions for Datapunk Services

This module defines the core error types and classifications used across
the Datapunk platform. It provides a standardized way to categorize,
track, and handle errors throughout the service mesh.

Design Philosophy:
- Clear error categorization for proper handling
- Rich context for debugging and monitoring
- Standardized severity levels for alerting
- Support for distributed tracing

Integration Points:
- Service mesh error reporting
- Monitoring and alerting systems
- Distributed tracing
- Logging infrastructure

NOTE: When adding new error categories or severity levels, ensure they
are documented and handled appropriately in ErrorHandler implementations.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class ErrorSeverity(Enum):
    """
    Error severity levels for prioritization and alerting.
    
    Levels are used to:
    - Determine alerting thresholds
    - Set logging priorities
    - Configure monitoring rules
    
    IMPORTANT: Severity should reflect business impact:
    - DEBUG: Development-time issues
    - INFO: Expected error conditions
    - WARNING: Potential issues requiring attention
    - ERROR: Service degradation
    - CRITICAL: Service outage or data loss risk
    """
    DEBUG = "debug"     # Development-time debugging
    INFO = "info"       # Expected error conditions
    WARNING = "warning" # Potential issues requiring attention
    ERROR = "error"     # Service degradation
    CRITICAL = "critical" # Service outage or data loss risk

class ErrorCategory(Enum):
    """
    Error categories for routing and handling.
    
    Categories determine:
    - Error handling strategies
    - Recovery procedures
    - Retry policies
    - Monitoring rules
    
    NOTE: Categories are designed to align with service mesh
    error handling patterns and monitoring requirements.
    
    TODO: Add support for custom categories per service
    TODO: Implement category-specific retry policies
    """
    AUTHENTICATION = "authentication"   # Identity verification failures
    AUTHORIZATION = "authorization"     # Permission check failures
    VALIDATION = "validation"          # Input/data validation errors
    NETWORK = "network"                # Network connectivity issues
    DATABASE = "database"              # Database operation failures
    CACHE = "cache"                    # Cache operation failures
    RESOURCE = "resource"              # Resource availability issues
    CONFIGURATION = "configuration"     # System configuration problems
    BUSINESS_LOGIC = "business_logic"  # Application logic errors
    EXTERNAL_SERVICE = "external_service" # External service failures
    RATE_LIMIT = "rate_limit"          # Rate limiting violations
    TIMEOUT = "timeout"                # Operation timeout errors

@dataclass
class ErrorContext:
    """
    Rich context for error tracking and debugging.
    
    Provides:
    - Service identification
    - Operation tracing
    - Request correlation
    - User context
    - Timing information
    
    IMPORTANT: Sensitive data in additional_data should be
    redacted before logging or transmission.
    
    NOTE: Context is designed to support distributed tracing
    and cross-service error correlation.
    """
    service_id: str          # Originating service identifier
    operation: str           # Operation that failed
    trace_id: str           # Distributed tracing correlation ID
    timestamp: float        # Error occurrence time
    request_id: Optional[str] = None  # Original request identifier
    user_id: Optional[str] = None     # Affected user (if applicable)
    additional_data: Optional[Dict[str, Any]] = None  # Extra debug info

@dataclass
class ServiceError(Exception):
    """
    Standard error type for Datapunk services.
    
    Features:
    - Standardized error classification
    - Rich context for debugging
    - Retry policy indication
    - HTTP status mapping
    - Original error preservation
    
    Usage:
    ```python
    raise ServiceError(
        code="USER_NOT_FOUND",
        message="User does not exist",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        context=error_context,
        retry_allowed=False
    )
    ```
    
    NOTE: The code field should follow the format:
    DOMAIN_SPECIFIC_ERROR (e.g., USER_NOT_FOUND, DB_CONNECTION_FAILED)
    """
    code: str               # Unique error identifier
    message: str            # Human-readable error description
    category: ErrorCategory # Error classification
    severity: ErrorSeverity # Error severity level
    context: ErrorContext   # Error context for debugging
    retry_allowed: bool = True  # Whether retry should be attempted
    http_status: int = 500     # Mapped HTTP status code
    cause: Optional[Exception] = None  # Original exception if wrapped