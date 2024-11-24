"""Shared type definitions for auth components."""
from typing import TypeVar, Dict, Any, Optional, Union
from datetime import datetime

# Generic types
TPolicy = TypeVar('TPolicy')
TUser = TypeVar('TUser')

# Common type aliases
Metadata = Dict[str, Any]
Timestamp = datetime
ResourceID = str
UserID = str

# Auth types
AuthToken = str
AuthContext = Dict[str, Any]
AuthResult = Dict[str, Any]

# Validation types
ValidationContext = Dict[str, Any]
ValidationResult = Dict[str, bool]

# Policy types
PolicyContext = Dict[str, Any]
PolicyResult = Dict[str, Any]

# Audit types
AuditContext = Dict[str, Any]
AuditResult = Dict[str, Any]

# Common result type
Result = Dict[str, Union[bool, str, Dict[str, Any]]] 