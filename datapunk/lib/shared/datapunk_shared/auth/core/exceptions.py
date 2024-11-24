from typing import Optional, Dict, Any
from ...exceptions import BaseError

class AuthError(BaseError):
    """Base class for authentication/authorization errors.
    
    Serves as the foundation for all auth-related exceptions in the system.
    Inherits from BaseError to maintain consistent error handling patterns.
    """
    def __init__(self, 
                 message: str,
                 code: str = "AUTH_ERROR",
                 details: Optional[Dict[str, Any]] = None):
        # Default code is AUTH_ERROR to distinguish auth failures from other system errors
        super().__init__(message, code, details)

class AccessDeniedError(AuthError):
    """Raised when access to a resource is denied.
    
    Used when a user attempts to perform an action they don't have permission for.
    Provides specific context about the resource and attempted action for debugging
    and audit logging purposes.
    """
    def __init__(self,
                 resource: str,
                 action: str,
                 details: Optional[Dict[str, Any]] = None):
        # Constructs a clear error message identifying both resource and attempted action
        message = f"Access denied to {resource} for action {action}"
        super().__init__(message, "ACCESS_DENIED", details)

class InvalidRoleError(AuthError):
    """Raised when role configuration is invalid.
    
    Indicates issues with role definitions or configurations in the system.
    Used during role validation, creation, or updates to catch malformed roles
    before they affect the authorization system.
    """
    def __init__(self,
                 role_name: str,
                 reason: str,
                 details: Optional[Dict[str, Any]] = None):
        # Includes both role name and specific reason for invalidity
        message = f"Invalid role {role_name}: {reason}"
        super().__init__(message, "INVALID_ROLE", details)

class RoleNotFoundError(AuthError):
    """Raised when a role cannot be found.
    
    Used when attempting to access, modify, or assign a role that doesn't exist
    in the system. Critical for maintaining role-based access control integrity.
    """
    def __init__(self,
                 role_name: str,
                 details: Optional[Dict[str, Any]] = None):
        # Simple but specific message indicating which role is missing
        message = f"Role {role_name} not found"
        super().__init__(message, "ROLE_NOT_FOUND", details) 