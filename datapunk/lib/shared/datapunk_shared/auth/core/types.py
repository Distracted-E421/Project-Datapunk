"""
Core authentication and authorization types for the Datapunk framework.

This module defines the fundamental types and data structures used throughout
the authentication and authorization system. It provides a type-safe foundation
for implementing access control, authentication flows, and audit logging.

Key components:
- Resource and access control enums
- Context objects for auth decisions
- Result objects for auth operations
- Type aliases for common auth-related identifiers

Security considerations:
- All sensitive data should be handled according to security best practices
- Token and credential information should never be logged in plain text
- Access levels follow the principle of least privilege
"""

from typing import Dict, List, Optional, Union, Any, TypeVar
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# Type variable for generic type hints, used in utility functions
# throughout the auth system
T = TypeVar('T')

# Type aliases for domain-specific identifiers
# These provide semantic meaning and allow for future type implementation changes
UserID = str       # Unique identifier for users
RoleID = str       # Unique identifier for roles
ResourceID = str   # Unique identifier for protected resources
PermissionID = str # Unique identifier for individual permissions
TokenID = str      # Unique identifier for auth tokens
SessionID = str    # Unique identifier for user sessions
RequestID = str    # Unique identifier for individual requests
ClientID = str     # Unique identifier for client applications

class ResourceType(Enum):
    """
    Types of protected resources within the system.
    
    Used for access control decisions and audit logging.
    New resource types should be added here when introducing new
    protected subsystems.
    """
    API = "api"           # REST/GraphQL API endpoints
    DATABASE = "database" # Database access points
    STORAGE = "storage"   # File storage systems
    COMPUTE = "compute"   # Computation resources
    ANALYTICS = "analytics" # Analytics dashboards and reports
    ADMIN = "admin"      # Administrative interfaces
    SERVICE = "service"  # Internal service endpoints
    STREAM = "stream"    # Real-time data streams
    MODEL = "model"      # ML models and predictions
    CACHE = "cache"      # Caching systems

class AccessLevel(Enum):
    """
    Hierarchical access levels for resource permissions.
    
    Levels are ordered from least to most privileged.
    Each level implicitly includes all lower levels.
    SYSTEM level should be used sparingly and only for critical operations.
    """
    NONE = 0    # No access granted
    READ = 10   # Read-only access
    WRITE = 20  # Read and write access
    DELETE = 30 # Read, write, and delete access
    ADMIN = 40  # Full administrative access
    SYSTEM = 50 # System-level access (use with caution)

class AuthStatus(Enum):
    """
    Possible authentication status results.
    
    Used to track the outcome of authentication attempts
    and manage session states.
    """
    SUCCESS = "success" # Authentication successful
    FAILED = "failed"   # Authentication failed (invalid credentials)
    EXPIRED = "expired" # Valid credentials but expired
    REVOKED = "revoked" # Explicitly revoked access
    INVALID = "invalid" # Invalid or malformed credentials
    LOCKED = "locked"   # Account temporarily locked

@dataclass
class AccessContext:
    """
    Context for making access control decisions.
    
    Contains all relevant information needed to make an authorization
    decision for a specific resource access attempt.
    
    Note: client_ip should be validated and normalized before use
    """
    user_id: UserID
    roles: List[RoleID]
    resource_id: ResourceID
    resource_type: ResourceType
    access_level: AccessLevel
    client_ip: Optional[str] = None      # Normalized IP address
    client_id: Optional[str] = None      # OAuth2 client identifier
    session_id: Optional[str] = None     # Current session identifier
    request_id: Optional[str] = None     # Request tracing identifier
    timestamp: Optional[datetime] = None  # Time of access attempt
    metadata: Optional[Dict[str, Any]] = None  # Additional context

@dataclass
class AccessResult:
    """
    Result of an access control decision.
    
    Provides detailed information about why access was granted or denied.
    The context field can be used to pass additional information to
    handlers (e.g., required roles, missing permissions).
    """
    allowed: bool
    reason: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AuthContext:
    """Authentication context."""
    auth_type: str
    credentials: Dict[str, Any]
    client_ip: str
    user_agent: str
    timestamp: datetime
    request_id: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AuthResult:
    """Authentication result."""
    status: AuthStatus
    user_id: Optional[UserID] = None
    roles: Optional[List[RoleID]] = None
    token: Optional[TokenID] = None
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

# Type aliases for various operations
# These provide flexibility for future implementation changes
ValidationContext = Dict[str, Any]  # Context for validation operations
ValidationResult = Dict[str, Union[bool, List[str], Dict[str, Any]]]  # Validation outcomes

# Audit logging type aliases
AuditContext = Dict[str, Any]  # Context for audit log entries
AuditResult = Dict[str, Any]   # Result of audit log operations

# Generic result type for operations
Result = Dict[str, Union[bool, str, Dict[str, Any]]]

# Generic metadata type for extending objects with additional data
Metadata = Dict[str, Any] 