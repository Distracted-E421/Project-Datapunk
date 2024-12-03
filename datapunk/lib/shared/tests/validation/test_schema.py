import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.validation.schema import (
    SchemaValidator,
    SchemaConfig,
    SchemaDefinition,
    SchemaResult,
    SchemaError
)

@pytest.fixture
def schema_config():
    return SchemaConfig(
        name="test_schema",
        schemas=[
            SchemaDefinition(
                name="user",
                version="1.0",
                fields={
                    "id": {
                        "type": "string",
                        "required": True,
                        "pattern": r"^[a-zA-Z0-9-]+$"
                    },
                    "name": {
                        "type": "string",
                        "required": True,
                        "min_length": 2,
                        "max_length": 50
                    },
                    "email": {
                        "type": "string",
                        "required": True,
                        "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    },
                    "age": {
                        "type": "integer",
                        "required": False,
                        "min_value": 0,
                        "max_value": 150
                    },
                    "roles": {
                        "type": "array",
                        "required": False,
                        "items": {
                            "type": "string",
                            "enum": ["user", "admin", "moderator"]
                        }
                    },
                    "settings": {
                        "type": "object",
                        "required": False,
                        "properties": {
                            "theme": {
                                "type": "string",
                                "enum": ["light", "dark"]
                            },
                            "notifications": {
                                "type": "boolean"
                            }
                        }
                    }
                }
            )
        ],
        metrics_enabled=True
    )

@pytest.fixture
async def schema_validator(schema_config):
    validator = SchemaValidator(schema_config)
    await validator.initialize()
    return validator

@pytest.mark.asyncio
async def test_validator_initialization(schema_validator, schema_config):
    """Test schema validator initialization"""
    assert schema_validator.config == schema_config
    assert schema_validator.is_initialized
    assert len(schema_validator.schemas) == len(schema_config.schemas)

@pytest.mark.asyncio
async def test_valid_object_validation(schema_validator):
    """Test validation of valid object"""
    valid_user = {
        "id": "user-123",
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
        "roles": ["user", "admin"],
        "settings": {
            "theme": "dark",
            "notifications": True
        }
    }
    
    result = await schema_validator.validate("user", valid_user)
    assert result.is_valid
    assert not result.errors

@pytest.mark.asyncio
async def test_invalid_object_validation(schema_validator):
    """Test validation of invalid object"""
    invalid_user = {
        "id": "user@123",  # Invalid pattern
        "name": "J",  # Too short
        "email": "invalid-email",  # Invalid email
        "age": 200,  # Too high
        "roles": ["user", "invalid_role"],  # Invalid role
        "settings": {
            "theme": "custom",  # Not in enum
            "notifications": "yes"  # Wrong type
        }
    }
    
    result = await schema_validator.validate("user", invalid_user)
    assert not result.is_valid
    assert len(result.errors) > 0

@pytest.mark.asyncio
async def test_missing_required_fields(schema_validator):
    """Test validation with missing required fields"""
    incomplete_user = {
        "name": "John Doe"
        # Missing id and email
    }
    
    result = await schema_validator.validate("user", incomplete_user)
    assert not result.is_valid
    assert any("required" in str(err) for err in result.errors)

@pytest.mark.asyncio
async def test_additional_fields(schema_validator):
    """Test validation with additional fields"""
    user_with_extra = {
        "id": "user-123",
        "name": "John Doe",
        "email": "john@example.com",
        "unknown_field": "value"  # Additional field
    }
    
    result = await schema_validator.validate(
        "user",
        user_with_extra,
        allow_additional_fields=False
    )
    assert not result.is_valid
    assert any("additional" in str(err) for err in result.errors)

@pytest.mark.asyncio
async def test_nested_object_validation(schema_validator):
    """Test validation of nested objects"""
    # Add nested schema
    nested_schema = SchemaDefinition(
        name="organization",
        version="1.0",
        fields={
            "id": {"type": "string", "required": True},
            "name": {"type": "string", "required": True},
            "admin": {
                "type": "object",
                "required": True,
                "schema": "user"  # Reference to user schema
            }
        }
    )
    
    await schema_validator.add_schema(nested_schema)
    
    valid_org = {
        "id": "org-123",
        "name": "Test Org",
        "admin": {
            "id": "user-123",
            "name": "John Doe",
            "email": "john@example.com"
        }
    }
    
    result = await schema_validator.validate("organization", valid_org)
    assert result.is_valid

@pytest.mark.asyncio
async def test_array_validation(schema_validator):
    """Test validation of array fields"""
    # Add array schema
    array_schema = SchemaDefinition(
        name="team",
        version="1.0",
        fields={
            "name": {"type": "string", "required": True},
            "members": {
                "type": "array",
                "required": True,
                "min_items": 1,
                "max_items": 5,
                "items": {"schema": "user"}
            }
        }
    )
    
    await schema_validator.add_schema(array_schema)
    
    valid_team = {
        "name": "Test Team",
        "members": [
            {
                "id": "user-1",
                "name": "John Doe",
                "email": "john@example.com"
            },
            {
                "id": "user-2",
                "name": "Jane Doe",
                "email": "jane@example.com"
            }
        ]
    }
    
    result = await schema_validator.validate("team", valid_team)
    assert result.is_valid

@pytest.mark.asyncio
async def test_schema_metrics(schema_validator):
    """Test schema validation metrics"""
    metrics = []
    schema_validator.set_metrics_callback(metrics.append)
    
    valid_user = {
        "id": "user-123",
        "name": "John Doe",
        "email": "john@example.com"
    }
    
    await schema_validator.validate("user", valid_user)
    
    assert len(metrics) > 0
    assert any(m["type"] == "schema_validation" for m in metrics)
    assert any(m["type"] == "validation_success" for m in metrics)

@pytest.mark.asyncio
async def test_schema_versioning(schema_validator):
    """Test schema versioning"""
    # Add new version of user schema
    new_user_schema = SchemaDefinition(
        name="user",
        version="2.0",
        fields={
            "id": {"type": "string", "required": True},
            "name": {"type": "string", "required": True},
            "email": {"type": "string", "required": True},
            "profile": {  # New field
                "type": "object",
                "required": True,
                "properties": {
                    "bio": {"type": "string"},
                    "avatar": {"type": "string"}
                }
            }
        }
    )
    
    await schema_validator.add_schema(new_user_schema)
    
    # Test old version
    old_user = {
        "id": "user-123",
        "name": "John Doe",
        "email": "john@example.com"
    }
    
    result = await schema_validator.validate("user", old_user, version="1.0")
    assert result.is_valid
    
    # Test new version
    result = await schema_validator.validate("user", old_user, version="2.0")
    assert not result.is_valid  # Missing required profile

@pytest.mark.asyncio
async def test_custom_validation_rules(schema_validator):
    """Test custom validation rules"""
    # Add custom validation rule
    async def validate_password_strength(value, params):
        import re
        has_upper = bool(re.search(r'[A-Z]', value))
        has_lower = bool(re.search(r'[a-z]', value))
        has_digit = bool(re.search(r'\d', value))
        return has_upper and has_lower and has_digit
    
    schema_validator.add_validation_rule(
        "password_strength",
        validate_password_strength
    )
    
    # Add schema with custom rule
    password_schema = SchemaDefinition(
        name="credentials",
        version="1.0",
        fields={
            "username": {"type": "string", "required": True},
            "password": {
                "type": "string",
                "required": True,
                "custom_rules": ["password_strength"]
            }
        }
    )
    
    await schema_validator.add_schema(password_schema)
    
    # Test validation
    valid_creds = {
        "username": "john_doe",
        "password": "TestPass123"
    }
    
    result = await schema_validator.validate("credentials", valid_creds)
    assert result.is_valid
    
    invalid_creds = {
        "username": "john_doe",
        "password": "weakpass"
    }
    
    result = await schema_validator.validate("credentials", invalid_creds)
    assert not result.is_valid

@pytest.mark.asyncio
async def test_error_handling(schema_validator):
    """Test error handling"""
    # Test with non-existent schema
    with pytest.raises(SchemaError):
        await schema_validator.validate("non_existent", {})
    
    # Test with invalid schema version
    with pytest.raises(SchemaError):
        await schema_validator.validate("user", {}, version="999.0")