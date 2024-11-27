"""Hierarchical exception system for Datapunk service mesh.

This module implements a comprehensive exception hierarchy that supports the
error handling requirements defined in sys-arch.mmd. It provides structured
error reporting with error codes and detailed context for debugging.

Key Features:
- Hierarchical error classification
- Error code support for client handling
- Detailed error context capture
- Service mesh-specific error types
- Resource management errors

Implementation Notes:
- All exceptions inherit from DatapunkError base class
- Error codes are derived from class names by default
- Context details support arbitrary key-value pairs
- Designed for cross-service error propagation
"""

from typing import Optional, Dict, Any

class DatapunkError(Exception):
    """Base exception for all Datapunk errors.
    
    Provides structured error reporting with:
    - Error codes for client handling
    - Detailed context for debugging
    - Consistent error formatting
    
    Note: All service-specific exceptions should inherit from this class
    """
    def __init__(self, message: str, code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.code = code or self.__class__.__name__
        self.details = details or {}

# Service Mesh Errors
class MeshError(DatapunkError):
    """Base class for service mesh communication errors.
    
    Used for errors related to:
    - Service discovery
    - Load balancing
    - Circuit breaking
    - Retry handling
    
    Note: These errors typically indicate infrastructure issues
    """
    pass

class ServiceDiscoveryError(MeshError):
    """Raised when service discovery operations fail.
    
    Indicates issues with:
    - Service registration
    - Service lookup
    - DNS resolution
    - Health check integration
    """
    pass

class LoadBalancerError(MeshError):
    """Raised when load balancing operations fail.
    
    Indicates issues with:
    - Backend selection
    - Connection distribution
    - Health check integration
    """
    pass

class CircuitBreakerError(MeshError):
    """Raised when circuit breaker triggers.
    
    Indicates:
    - Service is in failure state
    - Requests are being blocked
    - Circuit is open
    """
    pass

class RetryError(MeshError):
    """Raised when retry policy is exhausted.
    
    Indicates:
    - Maximum retries reached
    - Backoff strategy failed
    - Operation deemed unrecoverable
    """
    pass

# Cache Errors
class CacheError(DatapunkError):
    """Base class for caching system errors.
    
    Used for errors related to:
    - Cache operations
    - Connection management
    - Data serialization
    """
    pass

class CacheConnectionError(CacheError):
    """Raised when cache connection fails.
    
    Indicates issues with:
    - Connection establishment
    - Authentication
    - Network connectivity
    """
    pass

class CacheWriteError(CacheError):
    """Raised when cache write operations fail.
    
    Indicates issues with:
    - Data serialization
    - Storage capacity
    - Write permissions
    """
    pass

# Authentication Errors
class AuthError(DatapunkError):
    """Base class for authentication and authorization errors.
    
    Used for errors related to:
    - User authentication
    - Permission checking
    - Token validation
    """
    pass

class TokenError(AuthError):
    """Raised for token-related failures.
    
    Indicates issues with:
    - Token validation
    - Token expiration
    - Token refresh
    """
    pass

class PermissionError(AuthError):
    """Raised for permission-related failures.
    
    Indicates issues with:
    - Access control
    - Role validation
    - Resource permissions
    """
    pass

# Database Errors
class DatabaseError(DatapunkError):
    """Base class for database operation errors.
    
    Used for errors related to:
    - Query execution
    - Connection management
    - Transaction handling
    """
    pass

class ConnectionError(DatabaseError):
    """Raised when database connection fails.
    
    Indicates issues with:
    - Connection establishment
    - Authentication
    - Network connectivity
    """
    pass

class QueryError(DatabaseError):
    """Raised when query execution fails.
    
    Indicates issues with:
    - SQL syntax
    - Constraint violations
    - Resource limits
    """
    pass

# Validation Errors
class ValidationError(DatapunkError):
    """Base class for data validation errors.
    
    Used for errors related to:
    - Schema validation
    - Data format checking
    - Business rule validation
    """
    pass

class SchemaError(ValidationError):
    """Raised when schema validation fails.
    
    Indicates issues with:
    - Data structure
    - Field types
    - Required fields
    """
    pass

class InputError(ValidationError):
    """Raised when input validation fails.
    
    Indicates issues with:
    - Data format
    - Value ranges
    - Business rules
    """
    pass

# Resource Errors
class ResourceError(DatapunkError):
    """Base class for resource-related errors.
    
    Used for errors related to:
    - Resource allocation
    - Resource limits
    - Resource availability
    """
    pass

class ResourceNotFoundError(ResourceError):
    """Raised when requested resource is not found.
    
    Indicates issues with:
    - Resource lookup
    - Resource deletion
    - Resource availability
    """
    pass

class ResourceExhaustedError(ResourceError):
    """Raised when resource limits are exceeded.
    
    Indicates issues with:
    - Quota limits
    - Rate limits
    - Capacity limits
    """
    pass

# Configuration Errors
class ConfigError(DatapunkError):
    """Base class for configuration errors.
    
    Used for errors related to:
    - Config loading
    - Config validation
    - Config updates
    """
    pass

class MissingConfigError(ConfigError):
    """Raised when required configuration is missing.
    
    Indicates issues with:
    - Required settings
    - Environment variables
    - Config files
    """
    pass

class InvalidConfigError(ConfigError):
    """Raised when configuration is invalid.
    
    Indicates issues with:
    - Config format
    - Value validation
    - Dependency conflicts
    """
    pass 