"""
Core Validation Tests
----------------

Tests the core validation system including:
- Schema validation
- Data validation
- Rule enforcement
- Custom validators
- Error handling
- Performance monitoring
- Security controls

Run with: pytest -v test_validation.py
"""

import pytest
from datetime import datetime, timedelta
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from datapunk_shared.auth.core.validation import (
    Validator,
    ValidationRule,
    ValidationSchema,
    ValidationResult,
    ValidationError,
    SchemaRegistry,
    RuleEngine
)

# Test Fixtures

@pytest.fixture
def validator():
    """Create validator for testing."""
    return Validator()

@pytest.fixture
def schema_registry():
    """Create schema registry for testing."""
    return SchemaRegistry()

@pytest.fixture
def rule_engine():
    """Create rule engine for testing."""
    return RuleEngine()

@pytest.fixture
def test_schema():
    """Create test schema for testing."""
    return ValidationSchema(
        name="test_schema",
        fields={
            "id": {"type": "string", "required": True},
            "name": {"type": "string", "min_length": 3},
            "age": {"type": "integer", "min": 0},
            "email": {"type": "string", "pattern": r"^[^@]+@[^@]+\.[^@]+$"}
        }
    )

# Schema Validation Tests

def test_schema_validation(validator, test_schema):
    """Test schema validation."""
    # Valid data
    valid_data = {
        "id": "123",
        "name": "Test",
        "age": 25,
        "email": "test@example.com"
    }
    result = validator.validate(valid_data, test_schema)
    assert result.is_valid is True
    assert len(result.errors) == 0
    
    # Invalid data
    invalid_data = {
        "name": "T",  # Too short
        "age": -1,    # Negative
        "email": "invalid-email"  # Invalid format
    }
    result = validator.validate(invalid_data, test_schema)
    assert result.is_valid is False
    assert len(result.errors) == 4  # Missing id, short name, negative age, invalid email

def test_nested_schema_validation(validator):
    """Test nested schema validation."""
    nested_schema = ValidationSchema(
        name="nested_schema",
        fields={
            "user": {
                "type": "object",
                "fields": {
                    "id": {"type": "string"},
                    "profile": {
                        "type": "object",
                        "fields": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"}
                        }
                    }
                }
            }
        }
    )
    
    # Valid nested data
    valid_data = {
        "user": {
            "id": "123",
            "profile": {
                "name": "Test",
                "age": 25
            }
        }
    }
    result = validator.validate(valid_data, nested_schema)
    assert result.is_valid is True
    
    # Invalid nested data
    invalid_data = {
        "user": {
            "id": "123",
            "profile": {
                "name": "Test",
                "age": "invalid"  # Should be integer
            }
        }
    }
    result = validator.validate(invalid_data, nested_schema)
    assert result.is_valid is False
    assert "age" in str(result.errors[0])

# Data Validation Tests

def test_type_validation(validator):
    """Test type validation."""
    schema = ValidationSchema(
        name="type_schema",
        fields={
            "string_field": {"type": "string"},
            "int_field": {"type": "integer"},
            "float_field": {"type": "float"},
            "bool_field": {"type": "boolean"},
            "list_field": {"type": "array"},
            "dict_field": {"type": "object"}
        }
    )
    
    # Valid types
    valid_data = {
        "string_field": "test",
        "int_field": 123,
        "float_field": 123.45,
        "bool_field": True,
        "list_field": [1, 2, 3],
        "dict_field": {"key": "value"}
    }
    result = validator.validate(valid_data, schema)
    assert result.is_valid is True
    
    # Invalid types
    invalid_data = {
        "string_field": 123,
        "int_field": "123",
        "float_field": "123.45",
        "bool_field": "true",
        "list_field": "not_a_list",
        "dict_field": "not_a_dict"
    }
    result = validator.validate(invalid_data, schema)
    assert result.is_valid is False
    assert len(result.errors) == 6

def test_constraint_validation(validator):
    """Test constraint validation."""
    schema = ValidationSchema(
        name="constraint_schema",
        fields={
            "string": {
                "type": "string",
                "min_length": 3,
                "max_length": 10,
                "pattern": r"^[a-zA-Z]+$"
            },
            "number": {
                "type": "integer",
                "min": 0,
                "max": 100,
                "multiple_of": 5
            },
            "list": {
                "type": "array",
                "min_items": 1,
                "max_items": 5,
                "unique_items": True
            }
        }
    )
    
    # Valid constraints
    valid_data = {
        "string": "Test",
        "number": 25,
        "list": [1, 2, 3]
    }
    result = validator.validate(valid_data, schema)
    assert result.is_valid is True
    
    # Invalid constraints
    invalid_data = {
        "string": "A1",  # Too short and contains number
        "number": 123,   # Too large
        "list": [1, 1]   # Duplicate items
    }
    result = validator.validate(invalid_data, schema)
    assert result.is_valid is False
    assert len(result.errors) == 4

# Custom Validation Tests

def test_custom_validator(validator):
    """Test custom validator implementation."""
    def validate_password(value: str) -> bool:
        """Custom password validator."""
        has_upper = any(c.isupper() for c in value)
        has_lower = any(c.islower() for c in value)
        has_digit = any(c.isdigit() for c in value)
        return has_upper and has_lower and has_digit
    
    schema = ValidationSchema(
        name="password_schema",
        fields={
            "password": {
                "type": "string",
                "custom_validator": validate_password
            }
        }
    )
    
    # Valid password
    result = validator.validate({"password": "Test123"}, schema)
    assert result.is_valid is True
    
    # Invalid password
    result = validator.validate({"password": "weakpass"}, schema)
    assert result.is_valid is False

def test_custom_error_messages(validator):
    """Test custom error messages."""
    schema = ValidationSchema(
        name="custom_errors",
        fields={
            "age": {
                "type": "integer",
                "min": 18,
                "error_messages": {
                    "type": "Age must be a number",
                    "min": "Must be 18 or older"
                }
            }
        }
    )
    
    # Type error
    result = validator.validate({"age": "invalid"}, schema)
    assert "must be a number" in str(result.errors[0]).lower()
    
    # Min value error
    result = validator.validate({"age": 16}, schema)
    assert "must be 18 or older" in str(result.errors[0]).lower()

# Rule Engine Tests

def test_rule_engine(rule_engine):
    """Test rule engine."""
    # Define rules
    rules = [
        ValidationRule(
            name="age_rule",
            condition=lambda x: x.get("age", 0) >= 18,
            error="Must be 18 or older"
        ),
        ValidationRule(
            name="email_rule",
            condition=lambda x: "@" in x.get("email", ""),
            error="Invalid email format"
        )
    ]
    
    # Valid data
    valid_data = {"age": 20, "email": "test@example.com"}
    result = rule_engine.evaluate(valid_data, rules)
    assert result.is_valid is True
    
    # Invalid data
    invalid_data = {"age": 16, "email": "invalid"}
    result = rule_engine.evaluate(invalid_data, rules)
    assert result.is_valid is False
    assert len(result.errors) == 2

# Schema Registry Tests

def test_schema_registry(schema_registry, test_schema):
    """Test schema registry."""
    # Register schema
    schema_registry.register(test_schema)
    assert "test_schema" in schema_registry.schemas
    
    # Get schema
    retrieved = schema_registry.get("test_schema")
    assert retrieved.name == test_schema.name
    assert retrieved.fields == test_schema.fields
    
    # Register duplicate
    with pytest.raises(ValueError):
        schema_registry.register(test_schema)

def test_schema_inheritance(schema_registry):
    """Test schema inheritance."""
    # Base schema
    base_schema = ValidationSchema(
        name="base",
        fields={
            "id": {"type": "string"},
            "created_at": {"type": "datetime"}
        }
    )
    
    # Extended schema
    extended_schema = ValidationSchema(
        name="extended",
        fields={
            "name": {"type": "string"}
        },
        inherit_from="base"
    )
    
    # Register schemas
    schema_registry.register(base_schema)
    schema_registry.register(extended_schema)
    
    # Validate with inherited fields
    validator = Validator(schema_registry=schema_registry)
    result = validator.validate({
        "id": "123",
        "created_at": datetime.utcnow(),
        "name": "Test"
    }, extended_schema)
    assert result.is_valid is True

# Performance Tests

def test_validation_performance(validator, test_schema):
    """Test validation performance."""
    # Generate test data
    data_list = [
        {
            "id": str(i),
            "name": f"Test {i}",
            "age": 20 + i % 50,
            "email": f"test{i}@example.com"
        }
        for i in range(1000)
    ]
    
    # Measure validation time
    start_time = datetime.utcnow()
    results = [validator.validate(data, test_schema) for data in data_list]
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 1.0  # Should validate 1000 items within 1 second
    assert all(r.is_valid for r in results)

def test_schema_compilation(validator):
    """Test schema compilation optimization."""
    # Create complex schema
    schema = ValidationSchema(
        name="complex",
        fields={
            "nested": {
                "type": "object",
                "fields": {
                    "array": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "fields": {
                                "id": {"type": "string"},
                                "value": {"type": "integer"}
                            }
                        }
                    }
                }
            }
        }
    )
    
    # Compile schema
    compiled = validator.compile_schema(schema)
    
    # Validate with compiled schema
    start_time = datetime.utcnow()
    for _ in range(1000):
        validator.validate_compiled({
            "nested": {
                "array": [
                    {"id": "1", "value": 1},
                    {"id": "2", "value": 2}
                ]
            }
        }, compiled)
    end_time = datetime.utcnow()
    
    # Verify compilation improves performance
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 0.5  # Should be faster than uncompiled 