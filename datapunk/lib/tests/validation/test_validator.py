import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.validation.validator import (
    DataValidator,
    ValidationConfig,
    ValidationRule,
    ValidationResult,
    ValidationError
)

@pytest.fixture
def validation_config():
    return ValidationConfig(
        name="test_validator",
        rules=[
            ValidationRule(
                name="string_length",
                type="string",
                params={
                    "min_length": 3,
                    "max_length": 50
                }
            ),
            ValidationRule(
                name="number_range",
                type="number",
                params={
                    "min_value": 0,
                    "max_value": 100
                }
            ),
            ValidationRule(
                name="email_format",
                type="pattern",
                params={
                    "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                }
            )
        ],
        custom_validators={},
        metrics_enabled=True
    )

@pytest.fixture
async def data_validator(validation_config):
    validator = DataValidator(validation_config)
    await validator.initialize()
    return validator

@pytest.mark.asyncio
async def test_validator_initialization(data_validator, validation_config):
    """Test validator initialization"""
    assert data_validator.config == validation_config
    assert data_validator.is_initialized
    assert len(data_validator.rules) == len(validation_config.rules)

@pytest.mark.asyncio
async def test_string_validation(data_validator):
    """Test string validation rules"""
    # Valid string
    result = await data_validator.validate_field(
        "test_string",
        "Hello World",
        "string_length"
    )
    assert result.is_valid
    
    # Too short
    result = await data_validator.validate_field(
        "test_string",
        "Hi",
        "string_length"
    )
    assert not result.is_valid
    assert "length" in str(result.errors[0])
    
    # Too long
    result = await data_validator.validate_field(
        "test_string",
        "x" * 51,
        "string_length"
    )
    assert not result.is_valid
    assert "length" in str(result.errors[0])

@pytest.mark.asyncio
async def test_number_validation(data_validator):
    """Test number validation rules"""
    # Valid number
    result = await data_validator.validate_field(
        "test_number",
        50,
        "number_range"
    )
    assert result.is_valid
    
    # Too small
    result = await data_validator.validate_field(
        "test_number",
        -1,
        "number_range"
    )
    assert not result.is_valid
    assert "minimum" in str(result.errors[0])
    
    # Too large
    result = await data_validator.validate_field(
        "test_number",
        101,
        "number_range"
    )
    assert not result.is_valid
    assert "maximum" in str(result.errors[0])

@pytest.mark.asyncio
async def test_pattern_validation(data_validator):
    """Test pattern validation rules"""
    # Valid email
    result = await data_validator.validate_field(
        "test_email",
        "test@example.com",
        "email_format"
    )
    assert result.is_valid
    
    # Invalid email
    result = await data_validator.validate_field(
        "test_email",
        "invalid-email",
        "email_format"
    )
    assert not result.is_valid
    assert "pattern" in str(result.errors[0])

@pytest.mark.asyncio
async def test_object_validation(data_validator):
    """Test object validation"""
    test_object = {
        "name": "John Doe",
        "age": 25,
        "email": "john@example.com"
    }
    
    rules = {
        "name": "string_length",
        "age": "number_range",
        "email": "email_format"
    }
    
    result = await data_validator.validate_object(test_object, rules)
    assert result.is_valid
    assert not result.errors

@pytest.mark.asyncio
async def test_custom_validation_rule(data_validator):
    """Test custom validation rule"""
    # Add custom rule
    async def validate_phone(value, params):
        import re
        pattern = r'^\+\d{1,3}-\d{3}-\d{3}-\d{4}$'
        return bool(re.match(pattern, value))
    
    data_validator.add_rule(
        ValidationRule(
            name="phone_format",
            type="custom",
            params={"validator": validate_phone}
        )
    )
    
    # Test valid phone
    result = await data_validator.validate_field(
        "phone",
        "+1-555-123-4567",
        "phone_format"
    )
    assert result.is_valid
    
    # Test invalid phone
    result = await data_validator.validate_field(
        "phone",
        "invalid-phone",
        "phone_format"
    )
    assert not result.is_valid

@pytest.mark.asyncio
async def test_validation_metrics(data_validator):
    """Test validation metrics collection"""
    metrics = []
    data_validator.set_metrics_callback(metrics.append)
    
    await data_validator.validate_field(
        "test_string",
        "Hello World",
        "string_length"
    )
    
    assert len(metrics) > 0
    assert any(m["type"] == "validation_check" for m in metrics)
    assert any(m["type"] == "validation_success" for m in metrics)

@pytest.mark.asyncio
async def test_nested_object_validation(data_validator):
    """Test nested object validation"""
    test_object = {
        "user": {
            "name": "John Doe",
            "contact": {
                "email": "john@example.com",
                "age": 25
            }
        }
    }
    
    rules = {
        "user.name": "string_length",
        "user.contact.email": "email_format",
        "user.contact.age": "number_range"
    }
    
    result = await data_validator.validate_object(test_object, rules)
    assert result.is_valid
    assert not result.errors

@pytest.mark.asyncio
async def test_array_validation(data_validator):
    """Test array validation"""
    # Add array validation rule
    data_validator.add_rule(
        ValidationRule(
            name="string_array",
            type="array",
            params={
                "item_rule": "string_length",
                "min_items": 1,
                "max_items": 5
            }
        )
    )
    
    # Valid array
    result = await data_validator.validate_field(
        "names",
        ["John Doe", "Jane Doe"],
        "string_array"
    )
    assert result.is_valid
    
    # Too many items
    result = await data_validator.validate_field(
        "names",
        ["Name " + str(i) for i in range(6)],
        "string_array"
    )
    assert not result.is_valid

@pytest.mark.asyncio
async def test_conditional_validation(data_validator):
    """Test conditional validation"""
    # Add conditional rule
    async def validate_age_if_adult(value, params, context):
        if context.get("is_adult"):
            return value >= 18
        return True
    
    data_validator.add_rule(
        ValidationRule(
            name="conditional_age",
            type="custom",
            params={"validator": validate_age_if_adult}
        )
    )
    
    # Test adult age
    result = await data_validator.validate_field(
        "age",
        15,
        "conditional_age",
        context={"is_adult": True}
    )
    assert not result.is_valid
    
    result = await data_validator.validate_field(
        "age",
        20,
        "conditional_age",
        context={"is_adult": True}
    )
    assert result.is_valid

@pytest.mark.asyncio
async def test_validation_pipeline(data_validator):
    """Test validation pipeline with multiple rules"""
    # Add pipeline rule
    data_validator.add_rule(
        ValidationRule(
            name="username",
            type="pipeline",
            params={
                "rules": ["string_length", "custom_username"]
            }
        )
    )
    
    async def validate_username(value, params):
        return value.isalnum()  # Only alphanumeric
    
    data_validator.add_rule(
        ValidationRule(
            name="custom_username",
            type="custom",
            params={"validator": validate_username}
        )
    )
    
    # Valid username
    result = await data_validator.validate_field(
        "username",
        "johndoe123",
        "username"
    )
    assert result.is_valid
    
    # Invalid username (special characters)
    result = await data_validator.validate_field(
        "username",
        "john@doe",
        "username"
    )
    assert not result.is_valid

@pytest.mark.asyncio
async def test_error_handling(data_validator):
    """Test error handling"""
    # Test with invalid rule
    with pytest.raises(ValidationError):
        await data_validator.validate_field(
            "test",
            "value",
            "non_existent_rule"
        )
    
    # Test with invalid value type
    with pytest.raises(ValidationError):
        await data_validator.validate_field(
            "test_number",
            "not_a_number",
            "number_range"
        )

@pytest.mark.asyncio
async def test_validation_context(data_validator):
    """Test validation with context"""
    # Add context-aware rule
    async def validate_with_context(value, params, context):
        return value in context.get("allowed_values", [])
    
    data_validator.add_rule(
        ValidationRule(
            name="context_check",
            type="custom",
            params={"validator": validate_with_context}
        )
    )
    
    context = {"allowed_values": [1, 2, 3]}
    
    # Valid value
    result = await data_validator.validate_field(
        "number",
        2,
        "context_check",
        context=context
    )
    assert result.is_valid
    
    # Invalid value
    result = await data_validator.validate_field(
        "number",
        4,
        "context_check",
        context=context
    )
    assert not result.is_valid