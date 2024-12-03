"""
Audit Logger Tests
--------------

Tests the audit logging system including:
- Log entry creation
- Log level management
- Structured logging
- Log formatting
- Log filtering
- Performance monitoring
- Security controls

Run with: pytest -v test_audit_logger.py
"""

import pytest
from datetime import datetime
import json
from unittest.mock import AsyncMock, Mock, patch
import logging

from datapunk_shared.auth.audit.audit_logger import (
    AuditLogger,
    LogLevel,
    LogEntry,
    LogFormatter,
    LogFilter,
    LogMetrics,
    LogSecurity
)

# Test Fixtures

@pytest.fixture
def log_handler():
    """Mock log handler for testing."""
    handler = Mock()
    handler.handle = Mock()
    handler.flush = Mock()
    return handler

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.timing = AsyncMock()
    return client

@pytest.fixture
def audit_logger(log_handler, metrics_client):
    """Create audit logger for testing."""
    return AuditLogger(
        handler=log_handler,
        metrics=metrics_client,
        level=LogLevel.INFO
    )

@pytest.fixture
def log_entry():
    """Create log entry for testing."""
    return LogEntry(
        timestamp=datetime.utcnow(),
        level=LogLevel.INFO,
        message="Test log message",
        context={
            "user_id": "test_user",
            "action": "test_action"
        },
        metadata={
            "source": "test",
            "category": "test_category"
        }
    )

# Logging Tests

def test_log_creation(audit_logger, log_entry):
    """Test log entry creation."""
    result = audit_logger.log(log_entry)
    
    assert result.success is True
    assert result.entry_id is not None
    assert result.timestamp is not None
    
    # Verify handler called
    audit_logger.handler.handle.assert_called_once()
    
    # Verify metrics
    audit_logger.metrics.increment.assert_called_with(
        "logs_created",
        tags={"level": log_entry.level.name}
    )

def test_log_levels(audit_logger):
    """Test log level filtering."""
    # Set logger level to INFO
    audit_logger.set_level(LogLevel.INFO)
    
    # DEBUG should not be logged
    debug_entry = LogEntry(
        level=LogLevel.DEBUG,
        message="Debug message"
    )
    result = audit_logger.log(debug_entry)
    assert result.success is False
    assert audit_logger.handler.handle.call_count == 0
    
    # INFO should be logged
    info_entry = LogEntry(
        level=LogLevel.INFO,
        message="Info message"
    )
    result = audit_logger.log(info_entry)
    assert result.success is True
    assert audit_logger.handler.handle.call_count == 1

def test_structured_logging(audit_logger):
    """Test structured logging format."""
    entry = LogEntry(
        message="Test message",
        context={"key": "value"},
        metadata={"meta_key": "meta_value"}
    )
    
    result = audit_logger.log(entry)
    
    # Verify structured format
    log_data = audit_logger.handler.handle.call_args[0][0]
    assert isinstance(log_data, dict)
    assert log_data["message"] == "Test message"
    assert log_data["context"]["key"] == "value"
    assert log_data["metadata"]["meta_key"] == "meta_value"

# Formatting Tests

def test_log_formatting():
    """Test log formatter."""
    formatter = LogFormatter()
    
    entry = LogEntry(
        timestamp=datetime.utcnow(),
        level=LogLevel.INFO,
        message="Test message",
        context={"key": "value"}
    )
    
    formatted = formatter.format(entry)
    
    assert isinstance(formatted, str)
    assert "Test message" in formatted
    assert entry.timestamp.isoformat() in formatted
    assert "INFO" in formatted
    assert "key" in formatted
    assert "value" in formatted

def test_custom_formatting():
    """Test custom log formatting."""
    formatter = LogFormatter(
        template="${timestamp} [${level}] ${message} - ${context}"
    )
    
    entry = LogEntry(
        timestamp=datetime.utcnow(),
        level=LogLevel.INFO,
        message="Test message"
    )
    
    formatted = formatter.format(entry)
    assert formatted.startswith(entry.timestamp.isoformat())
    assert "[INFO]" in formatted
    assert "Test message" in formatted

# Filtering Tests

def test_log_filtering():
    """Test log filtering."""
    filter = LogFilter(
        min_level=LogLevel.INFO,
        include_sources=["test"],
        exclude_categories=["debug"]
    )
    
    # Should pass filter
    entry1 = LogEntry(
        level=LogLevel.INFO,
        message="Test",
        metadata={"source": "test", "category": "prod"}
    )
    assert filter.should_log(entry1) is True
    
    # Should not pass (wrong level)
    entry2 = LogEntry(
        level=LogLevel.DEBUG,
        message="Test"
    )
    assert filter.should_log(entry2) is False
    
    # Should not pass (excluded category)
    entry3 = LogEntry(
        level=LogLevel.INFO,
        message="Test",
        metadata={"category": "debug"}
    )
    assert filter.should_log(entry3) is False

def test_dynamic_filtering(audit_logger):
    """Test dynamic filter updates."""
    # Add filter
    audit_logger.add_filter(
        lambda entry: "error" not in entry.message.lower()
    )
    
    # Should be logged
    entry1 = LogEntry(message="Success message")
    result = audit_logger.log(entry1)
    assert result.success is True
    
    # Should not be logged
    entry2 = LogEntry(message="Error occurred")
    result = audit_logger.log(entry2)
    assert result.success is False

# Performance Tests

def test_logging_performance(audit_logger):
    """Test logging performance."""
    entries = [
        LogEntry(message=f"Test message {i}")
        for i in range(1000)
    ]
    
    start_time = datetime.utcnow()
    results = audit_logger.log_batch(entries)
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 1.0  # Should process 1000 logs within 1 second
    
    # Verify results
    assert len(results) == 1000
    assert all(r.success for r in results)
    
    # Verify batch optimization
    assert audit_logger.handler.handle.call_count < 10  # Should use batching

def test_metrics_collection(audit_logger, log_entry):
    """Test metrics collection."""
    audit_logger.log(log_entry)
    
    # Verify metrics
    audit_logger.metrics.increment.assert_has_calls([
        mock.call("logs_created", tags={"level": "INFO"}),
        mock.call("logs_by_category", tags={"category": "test_category"}),
        mock.call("logs_by_source", tags={"source": "test"})
    ])
    
    # Verify timing metrics
    audit_logger.metrics.timing.assert_called_with(
        "log_processing_time",
        mock.ANY
    )

# Security Tests

def test_sensitive_data_handling(audit_logger):
    """Test handling of sensitive data in logs."""
    entry = LogEntry(
        message="User logged in",
        context={
            "password": "secret123",
            "api_key": "key123",
            "user_id": "test_user"
        }
    )
    
    result = audit_logger.log(entry)
    
    # Verify sensitive data is redacted
    log_data = audit_logger.handler.handle.call_args[0][0]
    assert log_data["context"]["password"] == "[REDACTED]"
    assert log_data["context"]["api_key"] == "[REDACTED]"
    assert log_data["context"]["user_id"] == "test_user"  # Not sensitive

def test_security_controls(audit_logger):
    """Test security controls."""
    # Enable security controls
    audit_logger.enable_security()
    
    # Test PII handling
    entry = LogEntry(
        message="Profile updated",
        context={
            "email": "test@example.com",
            "ssn": "123-45-6789",
            "name": "Test User"
        }
    )
    
    result = audit_logger.log(entry)
    
    # Verify PII is protected
    log_data = audit_logger.handler.handle.call_args[0][0]
    assert log_data["context"]["email"] != "test@example.com"
    assert log_data["context"]["ssn"] != "123-45-6789"
    assert "REDACTED" in str(log_data) 