import pytest
from datapunk_shared.error.error_types import (
    ErrorSeverity,
    ErrorCategory,
    DatapunkError,
    ErrorContext
)

def test_error_severity_levels():
    # Test all severity levels are present
    assert ErrorSeverity.DEBUG.value == "debug"
    assert ErrorSeverity.INFO.value == "info"
    assert ErrorSeverity.WARNING.value == "warning"
    assert ErrorSeverity.ERROR.value == "error"
    assert ErrorSeverity.CRITICAL.value == "critical"

def test_error_category_validation():
    # Test error category validation and properties
    for category in ErrorCategory:
        assert isinstance(category.value, str)
        assert hasattr(category, 'description')
        assert isinstance(category.description, str)

def test_datapunk_error_creation():
    error = DatapunkError(
        message="Test error",
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.VALIDATION,
        context={"test_key": "test_value"}
    )
    
    assert error.message == "Test error"
    assert error.severity == ErrorSeverity.ERROR
    assert error.category == ErrorCategory.VALIDATION
    assert error.context == {"test_key": "test_value"}
    assert str(error) == "Test error"

def test_error_context_creation():
    context = ErrorContext(
        operation="test_operation",
        resource_id="test_resource",
        user_id="test_user",
        additional_data={"key": "value"}
    )
    
    assert context.operation == "test_operation"
    assert context.resource_id == "test_resource"
    assert context.user_id == "test_user"
    assert context.additional_data == {"key": "value"}

def test_error_context_serialization():
    context = ErrorContext(
        operation="test_operation",
        resource_id="test_resource"
    )
    
    serialized = context.to_dict()
    assert isinstance(serialized, dict)
    assert serialized["operation"] == "test_operation"
    assert serialized["resource_id"] == "test_resource"

def test_error_severity_comparison():
    # Test severity level comparisons
    assert ErrorSeverity.CRITICAL > ErrorSeverity.ERROR
    assert ErrorSeverity.ERROR > ErrorSeverity.WARNING
    assert ErrorSeverity.WARNING > ErrorSeverity.INFO
    assert ErrorSeverity.INFO > ErrorSeverity.DEBUG

def test_datapunk_error_with_cause():
    cause = ValueError("Original error")
    error = DatapunkError(
        message="Wrapped error",
        severity=ErrorSeverity.ERROR,
        category=ErrorCategory.SYSTEM,
        cause=cause
    )
    
    assert error.cause == cause
    assert "Wrapped error" in str(error)

def test_error_category_grouping():
    # Test error category grouping functionality
    validation_errors = [
        DatapunkError("Error 1", category=ErrorCategory.VALIDATION),
        DatapunkError("Error 2", category=ErrorCategory.VALIDATION)
    ]
    
    system_errors = [
        DatapunkError("Error 3", category=ErrorCategory.SYSTEM),
        DatapunkError("Error 4", category=ErrorCategory.SYSTEM)
    ]
    
    all_errors = validation_errors + system_errors
    
    # Group errors by category
    grouped = {}
    for error in all_errors:
        if error.category not in grouped:
            grouped[error.category] = []
        grouped[error.category].append(error)
    
    assert len(grouped[ErrorCategory.VALIDATION]) == 2
    assert len(grouped[ErrorCategory.SYSTEM]) == 2

def test_error_context_merging():
    context1 = ErrorContext(
        operation="op1",
        additional_data={"key1": "value1"}
    )
    
    context2 = ErrorContext(
        operation="op2",
        additional_data={"key2": "value2"}
    )
    
    # Test merging contexts
    merged = context1.merge(context2)
    assert merged.operation == "op2"  # Latest operation wins
    assert "key1" in merged.additional_data
    assert "key2" in merged.additional_data 