"""
Core Error Handling Tests
--------------------

Tests the core error handling system including:
- Error detection
- Error classification
- Error recovery
- Error reporting
- Metrics collection
- Logging integration
- Security controls

Run with: pytest -v test_error_handling.py
"""

import pytest
from datetime import datetime
import json
from unittest.mock import AsyncMock, Mock, patch

from datapunk_shared.auth.core.error_handling import (
    ErrorHandler,
    ErrorProcessor,
    ErrorRecovery,
    ErrorMetrics,
    ErrorContext,
    ErrorReport,
    RecoveryStrategy
)
from datapunk_shared.auth.core.exceptions import AuthError

# Test Fixtures

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.gauge = AsyncMock()
    client.timing = AsyncMock()
    return client

@pytest.fixture
def logger_client():
    """Mock logger client for testing."""
    client = Mock()
    client.error = Mock()
    client.warning = Mock()
    client.info = Mock()
    return client

@pytest.fixture
def error_handler(metrics_client, logger_client):
    """Create error handler for testing."""
    return ErrorHandler(
        metrics=metrics_client,
        logger=logger_client
    )

@pytest.fixture
def error_context():
    """Create error context for testing."""
    return ErrorContext(
        timestamp=datetime.utcnow(),
        error_id="test_error",
        source="test_service",
        severity="high",
        metadata={
            "user_id": "test_user",
            "action": "test_action"
        }
    )

# Error Detection Tests

def test_error_detection(error_handler):
    """Test error detection capabilities."""
    # Test known error
    error = AuthError("Test error")
    result = error_handler.detect_error(error)
    assert result.detected is True
    assert result.error_type == "auth_error"
    
    # Test unknown error
    error = Exception("Unknown error")
    result = error_handler.detect_error(error)
    assert result.detected is True
    assert result.error_type == "unknown"

def test_error_classification(error_handler):
    """Test error classification."""
    # Security error
    error = SecurityError("Security violation")
    classification = error_handler.classify_error(error)
    assert classification.category == "security"
    assert classification.severity == "high"
    
    # Validation error
    error = ValidationError("Invalid input")
    classification = error_handler.classify_error(error)
    assert classification.category == "validation"
    assert classification.severity == "medium"

# Error Processing Tests

@pytest.mark.asyncio
async def test_error_processing(error_handler, error_context):
    """Test error processing."""
    error = AuthError("Test error")
    
    result = await error_handler.process_error(error, error_context)
    
    assert result.processed is True
    assert result.error_id is not None
    assert result.timestamp is not None
    
    # Verify metrics
    error_handler.metrics.increment.assert_called_with(
        "errors_processed",
        tags={"type": "auth_error"}
    )
    
    # Verify logging
    error_handler.logger.error.assert_called_once()

@pytest.mark.asyncio
async def test_batch_processing(error_handler):
    """Test batch error processing."""
    errors = [
        (AuthError("Error 1"), ErrorContext()),
        (ValidationError("Error 2"), ErrorContext()),
        (SecurityError("Error 3"), ErrorContext())
    ]
    
    results = await error_handler.process_errors(errors)
    
    assert len(results) == 3
    assert all(r.processed for r in results)
    
    # Verify batch metrics
    error_handler.metrics.gauge.assert_called_with(
        "errors_batch_size",
        3
    )

# Error Recovery Tests

def test_recovery_strategy():
    """Test recovery strategy implementation."""
    strategy = RecoveryStrategy(
        max_retries=3,
        backoff_factor=2,
        timeout=30
    )
    
    assert strategy.should_retry(attempt=1)
    assert strategy.should_retry(attempt=2)
    assert strategy.should_retry(attempt=3)
    assert not strategy.should_retry(attempt=4)
    
    # Test backoff timing
    delay = strategy.get_delay(attempt=2)
    assert delay == 4  # 2^2 seconds

@pytest.mark.asyncio
async def test_error_recovery(error_handler):
    """Test error recovery process."""
    error = AuthError("Recoverable error")
    context = ErrorContext(recovery_enabled=True)
    
    recovery = ErrorRecovery(
        strategy=RecoveryStrategy(max_retries=3)
    )
    
    result = await error_handler.attempt_recovery(
        error,
        context,
        recovery
    )
    
    assert result.attempted is True
    assert result.success in [True, False]
    assert result.attempts > 0

# Error Reporting Tests

def test_error_report_generation(error_handler, error_context):
    """Test error report generation."""
    error = AuthError("Test error")
    
    report = error_handler.generate_report(error, error_context)
    
    assert isinstance(report, ErrorReport)
    assert report.error_type == "auth_error"
    assert report.timestamp is not None
    assert report.context == error_context
    assert "Test error" in report.message

def test_report_formatting():
    """Test error report formatting."""
    report = ErrorReport(
        error_type="test_error",
        message="Test message",
        timestamp=datetime.utcnow(),
        severity="high"
    )
    
    # JSON format
    json_data = report.to_json()
    assert isinstance(json_data, str)
    assert "test_error" in json_data
    assert "Test message" in json_data
    
    # Dict format
    dict_data = report.to_dict()
    assert isinstance(dict_data, dict)
    assert dict_data["error_type"] == "test_error"
    assert dict_data["severity"] == "high"

# Metrics Collection Tests

@pytest.mark.asyncio
async def test_metrics_collection(error_handler, error_context):
    """Test error metrics collection."""
    error = AuthError("Test error")
    
    await error_handler.process_error(error, error_context)
    
    # Verify metrics
    error_handler.metrics.increment.assert_has_calls([
        mock.call("errors_total", tags={"type": "auth_error"}),
        mock.call("errors_by_severity", tags={"severity": "high"}),
        mock.call("errors_by_source", tags={"source": "test_service"})
    ])
    
    # Verify timing metrics
    error_handler.metrics.timing.assert_called_with(
        "error_processing_time",
        mock.ANY,
        tags={"type": "auth_error"}
    )

@pytest.mark.asyncio
async def test_error_trends(error_handler):
    """Test error trend analysis."""
    # Generate error sequence
    for _ in range(10):
        await error_handler.process_error(
            AuthError("Test error"),
            ErrorContext(severity="high")
        )
    
    # Verify trend metrics
    error_handler.metrics.gauge.assert_called_with(
        "error_rate",
        mock.ANY,
        tags={"severity": "high"}
    )

# Logging Integration Tests

def test_logging_integration(error_handler, error_context):
    """Test logging integration."""
    error = AuthError("Test error")
    
    error_handler.log_error(error, error_context)
    
    # Verify log levels
    error_handler.logger.error.assert_called_once()
    assert "Test error" in error_handler.logger.error.call_args[0][0]
    assert "test_service" in str(error_handler.logger.error.call_args)

def test_log_formatting(error_handler):
    """Test error log formatting."""
    error = AuthError("Test error")
    context = ErrorContext(
        error_id="test_id",
        source="test_source"
    )
    
    formatted = error_handler.format_log_message(error, context)
    
    assert "test_id" in formatted
    assert "test_source" in formatted
    assert "Test error" in formatted
    assert isinstance(formatted, str)

# Security Tests

def test_sensitive_data_handling(error_handler):
    """Test handling of sensitive data in errors."""
    error = AuthError(
        "Authentication failed",
        context={
            "password": "secret123",
            "api_key": "key123",
            "user_id": "test_user"
        }
    )
    
    report = error_handler.generate_report(error, ErrorContext())
    
    # Verify sensitive data is redacted
    assert "secret123" not in str(report)
    assert "key123" not in str(report)
    assert "test_user" in str(report)  # Not sensitive

def test_security_level_handling(error_handler):
    """Test security level-based handling."""
    # High security error
    error = SecurityError(
        "Security breach",
        severity="critical"
    )
    
    result = error_handler.handle_security_error(error)
    
    assert result.notify_security is True
    assert result.block_access is True
    assert result.audit_log is True

# Performance Tests

@pytest.mark.asyncio
async def test_error_handling_performance(error_handler):
    """Test error handling performance."""
    errors = [
        (AuthError(f"Error {i}"), ErrorContext())
        for i in range(1000)
    ]
    
    start_time = datetime.utcnow()
    results = await error_handler.process_errors(errors)
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 5.0  # Should process 1000 errors within 5 seconds
    
    # Verify batch optimization
    assert error_handler.logger.error.call_count < 50  # Should use batching

@pytest.mark.asyncio
async def test_recovery_performance(error_handler):
    """Test recovery performance."""
    error = AuthError("Test error")
    context = ErrorContext(recovery_enabled=True)
    recovery = ErrorRecovery(
        strategy=RecoveryStrategy(max_retries=5)
    )
    
    start_time = datetime.utcnow()
    for _ in range(100):
        await error_handler.attempt_recovery(error, context, recovery)
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 1.0  # Should handle 100 recovery attempts within 1 second 