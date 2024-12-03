"""
Core Types Tests
-----------

Tests the core type system including:
- Type definitions
- Type validation
- Type conversion
- Type serialization
- Type inheritance
- Type constraints
- Type utilities

Run with: pytest -v test_types.py
"""

import pytest
from datetime import datetime, timedelta
import json
from typing import Optional, List, Dict, Any
from enum import Enum

from datapunk_shared.auth.core.types import (
    AuthType,
    UserType,
    ResourceType,
    ActionType,
    StatusType,
    TypeValidator,
    TypeConverter,
    TypeRegistry
)

# Test Fixtures

@pytest.fixture
def type_validator():
    """Create type validator for testing."""
    return TypeValidator()

@pytest.fixture
def type_converter():
    """Create type converter for testing."""
    return TypeConverter()

@pytest.fixture
def type_registry():
    """Create type registry for testing."""
    return TypeRegistry()

# Type Definition Tests

def test_auth_type_values():
    """Test auth type enumeration."""
    assert AuthType.BASIC.value == "basic"
    assert AuthType.TOKEN.value == "token"
    assert AuthType.SESSION.value == "session"
    assert AuthType.API_KEY.value == "api_key"
    
    # Verify all types are unique
    values = [t.value for t in AuthType]
    assert len(values) == len(set(values))

def test_user_type_values():
    """Test user type enumeration."""
    assert UserType.STANDARD.value == "standard"
    assert UserType.ADMIN.value == "admin"
    assert UserType.SYSTEM.value == "system"
    assert UserType.SERVICE.value == "service"
    
    # Verify hierarchy
    assert UserType.ADMIN > UserType.STANDARD
    assert UserType.SYSTEM > UserType.ADMIN
    assert UserType.SERVICE != UserType.STANDARD

def test_resource_type_values():
    """Test resource type enumeration."""
    assert ResourceType.FILE.value == "file"
    assert ResourceType.DATABASE.value == "database"
    assert ResourceType.API.value == "api"
    assert ResourceType.SERVICE.value == "service"
    
    # Verify categorization
    assert ResourceType.FILE.is_storage_type()
    assert ResourceType.DATABASE.is_storage_type()
    assert ResourceType.API.is_service_type()
    assert ResourceType.SERVICE.is_service_type()

def test_action_type_values():
    """Test action type enumeration."""
    assert ActionType.READ.value == "read"
    assert ActionType.WRITE.value == "write"
    assert ActionType.DELETE.value == "delete"
    assert ActionType.EXECUTE.value == "execute"
    
    # Verify permissions
    assert ActionType.WRITE > ActionType.READ
    assert ActionType.DELETE > ActionType.WRITE
    assert ActionType.EXECUTE.requires_elevated_privileges()

# Type Validation Tests

def test_type_validation(type_validator):
    """Test type validation."""
    # Valid types
    assert type_validator.validate(AuthType.BASIC, AuthType) is True
    assert type_validator.validate("admin", UserType) is True
    assert type_validator.validate("read", ActionType) is True
    
    # Invalid types
    assert type_validator.validate("invalid", AuthType) is False
    assert type_validator.validate(123, UserType) is False
    assert type_validator.validate(None, ActionType) is False

def test_complex_type_validation(type_validator):
    """Test complex type validation."""
    # Define complex type
    class ComplexType:
        def __init__(self, auth_type: AuthType, user_type: UserType):
            self.auth_type = auth_type
            self.user_type = user_type
    
    # Valid complex type
    complex_obj = ComplexType(AuthType.BASIC, UserType.STANDARD)
    assert type_validator.validate_complex(complex_obj) is True
    
    # Invalid complex type
    invalid_obj = ComplexType("invalid", "invalid")
    assert type_validator.validate_complex(invalid_obj) is False

def test_type_constraints(type_validator):
    """Test type constraints."""
    # Define constraints
    constraints = {
        "auth_type": {
            "allowed": [AuthType.TOKEN, AuthType.SESSION],
            "forbidden": [AuthType.BASIC]
        },
        "user_type": {
            "min_level": UserType.STANDARD,
            "max_level": UserType.ADMIN
        }
    }
    
    # Test constraints
    assert type_validator.check_constraints(AuthType.TOKEN, "auth_type", constraints)
    assert not type_validator.check_constraints(AuthType.BASIC, "auth_type", constraints)
    assert type_validator.check_constraints(UserType.STANDARD, "user_type", constraints)
    assert not type_validator.check_constraints(UserType.SYSTEM, "user_type", constraints)

# Type Conversion Tests

def test_type_conversion(type_converter):
    """Test type conversion."""
    # String to enum
    assert type_converter.to_enum("basic", AuthType) == AuthType.BASIC
    assert type_converter.to_enum("admin", UserType) == UserType.ADMIN
    
    # Enum to string
    assert type_converter.to_string(AuthType.BASIC) == "basic"
    assert type_converter.to_string(UserType.ADMIN) == "admin"
    
    # Invalid conversions
    with pytest.raises(ValueError):
        type_converter.to_enum("invalid", AuthType)
    with pytest.raises(ValueError):
        type_converter.to_string("not_an_enum")

def test_complex_conversion(type_converter):
    """Test complex type conversion."""
    # Convert dictionary to object
    data = {
        "auth_type": "token",
        "user_type": "admin",
        "status": "active"
    }
    
    converted = type_converter.dict_to_types(data)
    assert converted["auth_type"] == AuthType.TOKEN
    assert converted["user_type"] == UserType.ADMIN
    assert converted["status"] == StatusType.ACTIVE
    
    # Convert back to dictionary
    reconverted = type_converter.types_to_dict(converted)
    assert reconverted == data

# Type Registry Tests

def test_type_registration(type_registry):
    """Test type registration."""
    # Register custom type
    class CustomType(Enum):
        TYPE1 = "type1"
        TYPE2 = "type2"
    
    type_registry.register("custom", CustomType)
    assert "custom" in type_registry.types
    assert type_registry.get("custom") == CustomType
    
    # Register duplicate
    with pytest.raises(ValueError):
        type_registry.register("custom", CustomType)

def test_type_lookup(type_registry):
    """Test type lookup."""
    # Lookup existing type
    assert type_registry.get("auth") == AuthType
    assert type_registry.get("user") == UserType
    
    # Lookup non-existent type
    with pytest.raises(KeyError):
        type_registry.get("nonexistent")

def test_type_inheritance():
    """Test type inheritance."""
    # Define inherited type
    class ExtendedAuthType(AuthType):
        OAUTH = "oauth"
        SAML = "saml"
    
    # Verify inheritance
    assert hasattr(ExtendedAuthType, "BASIC")
    assert hasattr(ExtendedAuthType, "OAUTH")
    assert ExtendedAuthType.BASIC.value == "basic"
    assert ExtendedAuthType.OAUTH.value == "oauth"

# Type Serialization Tests

def test_type_serialization():
    """Test type serialization."""
    # Create complex object
    data = {
        "auth": AuthType.TOKEN,
        "user": UserType.ADMIN,
        "action": ActionType.WRITE,
        "timestamp": datetime.utcnow()
    }
    
    # Serialize
    serialized = json.dumps(data, default=lambda x: x.value if isinstance(x, Enum) else str(x))
    assert isinstance(serialized, str)
    
    # Deserialize
    deserialized = json.loads(serialized)
    assert deserialized["auth"] == AuthType.TOKEN.value
    assert deserialized["user"] == UserType.ADMIN.value
    assert deserialized["action"] == ActionType.WRITE.value

def test_type_format_validation():
    """Test type format validation."""
    validator = TypeValidator()
    
    # Test format patterns
    patterns = {
        "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "date": r"^\d{4}-\d{2}-\d{2}$"
    }
    
    # Valid formats
    assert validator.validate_format("123e4567-e89b-12d3-a456-426614174000", "uuid") is True
    assert validator.validate_format("test@example.com", "email") is True
    assert validator.validate_format("2023-01-01", "date") is True
    
    # Invalid formats
    assert validator.validate_format("invalid-uuid", "uuid") is False
    assert validator.validate_format("invalid-email", "email") is False
    assert validator.validate_format("2023/01/01", "date") is False

# Type Utility Tests

def test_type_comparison():
    """Test type comparison utilities."""
    # Compare types
    assert AuthType.TOKEN > AuthType.BASIC
    assert UserType.ADMIN > UserType.STANDARD
    assert ActionType.WRITE > ActionType.READ
    
    # Compare type levels
    assert UserType.get_level(UserType.ADMIN) > UserType.get_level(UserType.STANDARD)
    assert ActionType.get_level(ActionType.WRITE) > ActionType.get_level(ActionType.READ)

def test_type_operations():
    """Test type operations."""
    # Type combination
    combined = ActionType.combine_permissions([
        ActionType.READ,
        ActionType.WRITE
    ])
    assert ActionType.READ in combined
    assert ActionType.WRITE in combined
    
    # Type intersection
    intersection = ActionType.intersect_permissions([
        {ActionType.READ, ActionType.WRITE},
        {ActionType.WRITE, ActionType.EXECUTE}
    ])
    assert ActionType.WRITE in intersection
    assert ActionType.READ not in intersection 