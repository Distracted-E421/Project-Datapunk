from typing import Optional, Dict, Any

class DatapunkError(Exception):
    """Base exception for all Datapunk errors."""
    def __init__(self, message: str, code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.code = code or self.__class__.__name__
        self.details = details or {}

# Service Mesh Errors
class MeshError(DatapunkError):
    """Base class for service mesh errors."""
    pass

class ServiceDiscoveryError(MeshError):
    """Raised when service discovery fails."""
    pass

class LoadBalancerError(MeshError):
    """Raised when load balancing fails."""
    pass

class CircuitBreakerError(MeshError):
    """Raised when circuit breaker is open."""
    pass

class RetryError(MeshError):
    """Raised when retry policy fails."""
    pass

# Cache Errors
class CacheError(DatapunkError):
    """Base class for caching errors."""
    pass

class CacheConnectionError(CacheError):
    """Raised when cache connection fails."""
    pass

class CacheWriteError(CacheError):
    """Raised when cache write fails."""
    pass

# Authentication Errors
class AuthError(DatapunkError):
    """Base class for authentication errors."""
    pass

class TokenError(AuthError):
    """Raised for token-related errors."""
    pass

class PermissionError(AuthError):
    """Raised for permission-related errors."""
    pass

# Database Errors
class DatabaseError(DatapunkError):
    """Base class for database errors."""
    pass

class ConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass

class QueryError(DatabaseError):
    """Raised when query execution fails."""
    pass

# Validation Errors
class ValidationError(DatapunkError):
    """Base class for validation errors."""
    pass

class SchemaError(ValidationError):
    """Raised when schema validation fails."""
    pass

class InputError(ValidationError):
    """Raised when input validation fails."""
    pass

# Resource Errors
class ResourceError(DatapunkError):
    """Base class for resource-related errors."""
    pass

class ResourceNotFoundError(ResourceError):
    """Raised when resource is not found."""
    pass

class ResourceExhaustedError(ResourceError):
    """Raised when resource limits are exceeded."""
    pass

# Configuration Errors
class ConfigError(DatapunkError):
    """Base class for configuration errors."""
    pass

class MissingConfigError(ConfigError):
    """Raised when required configuration is missing."""
    pass

class InvalidConfigError(ConfigError):
    """Raised when configuration is invalid."""
    pass 