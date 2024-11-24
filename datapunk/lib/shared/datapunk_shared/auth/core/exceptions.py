from typing import Optional, Dict, Any
from ...exceptions import BaseError

class AuthError(BaseError):
    """Base class for authentication/authorization errors."""
    def __init__(self, 
                 message: str,
                 code: str = "AUTH_ERROR",
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class AccessDeniedError(AuthError):
    """Raised when access to a resource is denied."""
    def __init__(self,
                 resource: str,
                 action: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Access denied to {resource} for action {action}"
        super().__init__(message, "ACCESS_DENIED", details)

class InvalidRoleError(AuthError):
    """Raised when role configuration is invalid."""
    def __init__(self,
                 role_name: str,
                 reason: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Invalid role {role_name}: {reason}"
        super().__init__(message, "INVALID_ROLE", details)

class RoleNotFoundError(AuthError):
    """Raised when a role cannot be found."""
    def __init__(self,
                 role_name: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Role {role_name} not found"
        super().__init__(message, "ROLE_NOT_FOUND", details) 