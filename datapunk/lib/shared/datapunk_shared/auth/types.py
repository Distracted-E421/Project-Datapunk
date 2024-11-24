"""Shared type definitions for auth components.

This module defines core type definitions used across the authentication and authorization system.
It provides type hints and aliases to ensure consistency and type safety throughout the auth flow.

Key components:
- Generic type variables for policy and user objects
- Authentication and authorization context types
- Validation and policy evaluation types
- Audit logging type definitions
"""
from typing import TypeVar, Dict, Any, Optional, Union
from datetime import datetime

# Generic type variables for polymorphic auth components
TPolicy = TypeVar('TPolicy')  # Represents any policy implementation
TUser = TypeVar('TUser')      # Represents any user model implementation

# Core type aliases for common data structures
Metadata = Dict[str, Any]     # Flexible metadata container for extended attributes
Timestamp = datetime         # Standardized timestamp type for audit trails
ResourceID = str            # Unique identifier for protected resources
UserID = str               # Unique identifier for system users

# Authentication types
AuthToken = str            # JWT or other token format for auth credentials
AuthContext = Dict[str, Any]  # Contains auth request context (headers, claims, etc.)
AuthResult = Dict[str, Any]   # Stores auth operation results and metadata

# Input validation types
ValidationContext = Dict[str, Any]  # Context for input validation operations
ValidationResult = Dict[str, bool]  # Validation results with field-level outcomes

# Policy evaluation types
PolicyContext = Dict[str, Any]  # Context for policy evaluation (user, resource, action)
PolicyResult = Dict[str, Any]   # Policy evaluation outcome with reasoning

# Audit logging types
AuditContext = Dict[str, Any]  # Context for audit log entries
AuditResult = Dict[str, Any]   # Audit operation results and metadata

# Generic result type for operation outcomes
Result = Dict[str, Union[bool, str, Dict[str, Any]]]  # Standardized operation result
                                                      # Contains success flag, messages,
                                                      # and additional data 