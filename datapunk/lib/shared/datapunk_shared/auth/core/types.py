from typing import Dict, List, Optional, Union, Any, TypeVar
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

# Type variables for generics
T = TypeVar('T')

# Basic type aliases
UserID = str
RoleID = str
ResourceID = str
PermissionID = str
TokenID = str
SessionID = str
RequestID = str
ClientID = str

class ResourceType(Enum):
    """Types of protected resources."""
    API = "api"
    DATABASE = "database"
    STORAGE = "storage"
    COMPUTE = "compute"
    ANALYTICS = "analytics"
    ADMIN = "admin"
    SERVICE = "service"
    STREAM = "stream"
    MODEL = "model"
    CACHE = "cache"

class AccessLevel(Enum):
    """Access levels for resources."""
    NONE = 0
    READ = 10
    WRITE = 20
    DELETE = 30
    ADMIN = 40
    SYSTEM = 50

class AuthStatus(Enum):
    """Authentication status values."""
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"
    LOCKED = "locked"

@dataclass
class AccessContext:
    """Context for access control decisions."""
    user_id: UserID
    roles: List[RoleID]
    resource_id: ResourceID
    resource_type: ResourceType
    access_level: AccessLevel
    client_ip: Optional[str] = None
    client_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AccessResult:
    """Result of access control check."""
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

# Validation types
ValidationContext = Dict[str, Any]
ValidationResult = Dict[str, Union[bool, List[str], Dict[str, Any]]]

# Audit types
AuditContext = Dict[str, Any]
AuditResult = Dict[str, Any]

# Common result type
Result = Dict[str, Union[bool, str, Dict[str, Any]]]

# Metadata type
Metadata = Dict[str, Any] 