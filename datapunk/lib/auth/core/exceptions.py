from typing import Optional, Dict, Any
from ...exceptions import BaseError

# NOTE: This module implements a hierarchical exception system for authentication
# and authorization, following the principle of specific error types for precise
# error handling and logging. Each exception carries structured data to aid in
# debugging and audit trails.

class AuthError(BaseError):
    """Base class for authentication/authorization errors.
    
    Serves as the foundation for all auth-related exceptions in the system.
    Inherits from BaseError to maintain consistent error handling patterns.
    
    Design Notes:
    - Uses a default 'AUTH_ERROR' code to distinguish from other system errors
    - Supports optional details dictionary for additional context
    - Maintains consistent error structure across the auth system
    """
    def __init__(self, 
                 message: str,
                 code: str = "AUTH_ERROR",
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code, details)

class AccessDeniedError(AuthError):
    """Raised when access to a resource is denied.
    
    Used when a user attempts to perform an action they don't have permission for.
    Provides specific context about the resource and attempted action for debugging
    and audit logging purposes.
    
    Design Notes:
    - Captures both resource and action for complete audit context
    - Useful for security logging and access attempt tracking
    - Can be used for both RBAC and ABAC authorization models
    """
    def __init__(self,
                 resource: str,
                 action: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Access denied to {resource} for action {action}"
        super().__init__(message, "ACCESS_DENIED", details)

class InvalidRoleError(AuthError):
    """Raised when role configuration is invalid.
    
    Indicates issues with role definitions or configurations in the system.
    Used during role validation, creation, or updates to catch malformed roles
    before they affect the authorization system.
    
    Design Notes:
    - Helps prevent corrupted role configurations from entering the system
    - Used in role validation workflows and configuration updates
    - Includes specific reason for invalidity to aid in troubleshooting
    
    Example scenarios:
    - Circular role dependencies
    - Missing required permissions
    - Invalid permission formats
    """
    def __init__(self,
                 role_name: str,
                 reason: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Invalid role {role_name}: {reason}"
        super().__init__(message, "INVALID_ROLE", details)

class RoleNotFoundError(AuthError):
    """Raised when a role cannot be found.
    
    Used when attempting to access, modify, or assign a role that doesn't exist
    in the system. Critical for maintaining role-based access control integrity.
    
    Design Notes:
    - Distinguishes between invalid roles and non-existent roles
    - Important for role assignment and permission checking workflows
    - May indicate configuration issues or data synchronization problems
    
    Common scenarios:
    - Role deletion without proper cleanup
    - Configuration mismatches between services
    - Database inconsistencies
    """
    def __init__(self,
                 role_name: str,
                 details: Optional[Dict[str, Any]] = None):
        message = f"Role {role_name} not found"
        super().__init__(message, "ROLE_NOT_FOUND", details) 