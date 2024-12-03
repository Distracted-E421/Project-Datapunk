"""
Core Exceptions Tests
-----------------

Tests the core exception system including:
- Exception hierarchy
- Error codes
- Error messages
- Exception handling
- Error context

Run with: pytest -v test_exceptions.py
"""

import pytest
from datetime import datetime
import json

from datapunk_shared.auth.core.exceptions import (
    AuthError,
    ValidationError,
    ConfigError,
    SecurityError,
    RateLimitError,
    PermissionError,
    ResourceError,
    SessionError,
    ErrorCode,
    ErrorContext
)

# Exception Hierarchy Tests

def test_exception_hierarchy():
    """Test exception class hierarchy."""
    # All exceptions should inherit from AuthError
    assert issubclass(ValidationError, AuthError)
    assert issubclass(ConfigError, AuthError)
    assert issubclass(SecurityError, AuthError)
    assert issubclass(RateLimitError, AuthError)
    assert issubclass(PermissionError, AuthError)
    assert issubclass(ResourceError, AuthError)
    assert issubclass(SessionError, AuthError)

def test_error_codes():
    """Test error code enumeration."""
    # Verify error code values
    assert ErrorCode.VALIDATION_ERROR.value.startswith("VAL")
    assert ErrorCode.CONFIG_ERROR.value.startswith("CFG")
    assert ErrorCode.SECURITY_ERROR.value.startswith("SEC")
    assert ErrorCode.RATE_LIMIT_ERROR.value.startswith("RATE")
    assert ErrorCode.PERMISSION_ERROR.value.startswith("PERM")
    assert ErrorCode.RESOURCE_ERROR.value.startswith("RES")
    assert ErrorCode.SESSION_ERROR.value.startswith("SESS")
    
    # Verify code uniqueness
    codes = [code.value for code in ErrorCode]
    assert len(codes) == len(set(codes))

# Error Context Tests

def test_error_context_creation():
    """Test error context creation."""
    context = ErrorContext(
        timestamp=datetime.utcnow(),
        request_id="test_request",
        correlation_id="test_correlation",
        user_id="test_user",
        resource="test_resource",
        action="test_action",
        metadata={
            "source": "test",
            "severity": "high"
        }
    )
    
    assert context.request_id == "test_request"
    assert context.correlation_id == "test_correlation"
    assert context.user_id == "test_user"
    assert context.resource == "test_resource"
    assert context.action == "test_action"
    assert context.metadata["source"] == "test"

def test_error_context_validation():
    """Test error context validation."""
    # Invalid request ID
    with pytest.raises(ValueError):
        ErrorContext(request_id="")
    
    # Invalid correlation ID
    with pytest.raises(ValueError):
        ErrorContext(correlation_id="")
    
    # Invalid metadata
    with pytest.raises(ValueError):
        ErrorContext(metadata="invalid")  # Should be dict

def test_context_serialization():
    """Test error context serialization."""
    context = ErrorContext(
        request_id="test_request",
        correlation_id="test_correlation"
    )
    
    # Convert to dict
    data = context.to_dict()
    assert isinstance(data, dict)
    assert data["request_id"] == "test_request"
    assert data["correlation_id"] == "test_correlation"
    
    # Convert to JSON
    json_data = json.dumps(data)
    assert isinstance(json_data, str)
    
    # Deserialize
    loaded = ErrorContext.from_dict(json.loads(json_data))
    assert loaded.request_id == context.request_id
    assert loaded.correlation_id == context.correlation_id

# Exception Creation Tests

def test_validation_error():
    """Test validation error creation."""
    error = ValidationError(
        message="Invalid input",
        field="test_field",
        value="invalid_value",
        constraint="required"
    )
    
    assert error.code == ErrorCode.VALIDATION_ERROR
    assert error.field == "test_field"
    assert error.value == "invalid_value"
    assert error.constraint == "required"
    assert "Invalid input" in str(error)

def test_config_error():
    """Test configuration error creation."""
    error = ConfigError(
        message="Invalid config",
        parameter="test_param",
        value="invalid_value",
        expected="valid_value"
    )
    
    assert error.code == ErrorCode.CONFIG_ERROR
    assert error.parameter == "test_param"
    assert error.value == "invalid_value"
    assert error.expected == "valid_value"
    assert "Invalid config" in str(error)

def test_security_error():
    """Test security error creation."""
    error = SecurityError(
        message="Access denied",
        reason="invalid_token",
        severity="high"
    )
    
    assert error.code == ErrorCode.SECURITY_ERROR
    assert error.reason == "invalid_token"
    assert error.severity == "high"
    assert "Access denied" in str(error)

def test_rate_limit_error():
    """Test rate limit error creation."""
    error = RateLimitError(
        message="Too many requests",
        limit=100,
        current=150,
        reset_after=60
    )
    
    assert error.code == ErrorCode.RATE_LIMIT_ERROR
    assert error.limit == 100
    assert error.current == 150
    assert error.reset_after == 60
    assert "Too many requests" in str(error)

# Error Context Integration Tests

def test_error_with_context():
    """Test exception with error context."""
    context = ErrorContext(
        request_id="test_request",
        correlation_id="test_correlation"
    )
    
    error = ValidationError(
        message="Invalid input",
        field="test_field",
        context=context
    )
    
    assert error.context == context
    assert error.context.request_id == "test_request"
    assert error.context.correlation_id == "test_correlation"

def test_error_context_inheritance():
    """Test error context inheritance in exception chain."""
    parent_context = ErrorContext(
        request_id="parent_request",
        correlation_id="parent_correlation"
    )
    
    child_context = ErrorContext(
        request_id="child_request",
        correlation_id="child_correlation",
        parent_context=parent_context
    )
    
    error = ValidationError(
        message="Invalid input",
        context=child_context
    )
    
    assert error.context.parent_context == parent_context
    assert error.context.parent_context.request_id == "parent_request"

# Error Handling Tests

def test_error_handling():
    """Test error handling utilities."""
    try:
        raise ValidationError(
            message="Test error",
            field="test_field"
        )
    except AuthError as e:
        # Should be caught as AuthError
        assert isinstance(e, ValidationError)
        assert e.code == ErrorCode.VALIDATION_ERROR
        assert e.field == "test_field"
    
    try:
        raise SecurityError(
            message="Security error",
            reason="test_reason"
        )
    except AuthError as e:
        # Should be caught as AuthError
        assert isinstance(e, SecurityError)
        assert e.code == ErrorCode.SECURITY_ERROR
        assert e.reason == "test_reason"

def test_error_chaining():
    """Test exception chaining."""
    try:
        try:
            raise ValidationError("Inner error")
        except ValidationError as inner:
            raise SecurityError("Outer error") from inner
    except SecurityError as outer:
        assert isinstance(outer.__cause__, ValidationError)
        assert "Inner error" in str(outer.__cause__)
        assert "Outer error" in str(outer)

# Error Code Tests

def test_error_code_formatting():
    """Test error code formatting."""
    # Validation error code format
    error = ValidationError("Test error")
    assert error.code.value.startswith("VAL")
    assert len(error.code.value) >= 6  # Should include numeric suffix
    
    # Security error code format
    error = SecurityError("Test error")
    assert error.code.value.startswith("SEC")
    assert len(error.code.value) >= 6

def test_error_code_uniqueness():
    """Test error code uniqueness."""
    errors = [
        ValidationError("Test"),
        ValidationError("Test"),
        SecurityError("Test"),
        SecurityError("Test")
    ]
    
    # Each error should have a unique code
    codes = [e.code.value for e in errors]
    assert len(codes) == len(set(codes)) 