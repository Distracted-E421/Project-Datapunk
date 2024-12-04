"""
Audit System Tests
---------------

Tests the audit logging system including:
- Event logging and formatting
- Audit trail maintenance
- Compliance requirements
- Event filtering and searching
- Performance monitoring
- Security controls

Run with: pytest -v test_audit.py
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import json

from datapunk_shared.auth.audit import (
    AuditLogger, AuditEvent, AuditLevel,
    AuditFilter, ComplianceConfig,
    RetentionPolicy
)
from datapunk_shared.auth.audit.types import (
    EventID, EventType, EventSource,
    EventContext, EventMetadata
)

# Test Fixtures

@pytest.fixture
def storage_client():
    """Mock storage client for testing."""
    client = AsyncMock()
    client.store = AsyncMock()
    client.get = AsyncMock()
    client.search = AsyncMock()
    return client

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.timing = AsyncMock()
    return client

@pytest.fixture
def compliance_config():
    """Create compliance configuration for testing."""
    return ComplianceConfig(
        retention_period=timedelta(days=365),
        required_fields={"user_id", "action", "resource"},
        pii_fields={"email", "ip_address"},
        audit_level=AuditLevel.DETAILED
    )

@pytest.fixture
def retention_policy():
    """Create retention policy for testing."""
    return RetentionPolicy(
        default_retention=timedelta(days=90),
        compliance_retention=timedelta(days=365),
        security_retention=timedelta(days=730)
    )

@pytest.fixture
def audit_logger(storage_client, metrics_client, compliance_config, retention_policy):
    """Create audit logger instance for testing."""
    return AuditLogger(
        storage=storage_client,
        metrics=metrics_client,
        compliance=compliance_config,
        retention=retention_policy
    )

# Event Logging Tests

@pytest.mark.asyncio
async def test_log_event_success(audit_logger):
    """Test successful event logging."""
    event = AuditEvent(
        type=EventType.USER_ACTION,
        source=EventSource.API,
        action="login",
        user_id="test_user",
        resource="auth_service",
        metadata={
            "ip_address": "192.168.1.1",
            "user_agent": "test_browser"
        }
    )
    
    result = await audit_logger.log_event(event)
    
    assert result["event_id"]
    assert result["timestamp"]
    
    # Verify storage
    audit_logger.storage.store.assert_called_once()
    stored_event = audit_logger.storage.store.call_args[0][0]
    assert stored_event["type"] == EventType.USER_ACTION.value
    assert stored_event["user_id"] == "test_user"
    
    # Verify metrics
    audit_logger.metrics.increment.assert_called_with(
        "audit_events",
        tags={"type": EventType.USER_ACTION.value}
    )

@pytest.mark.asyncio
async def test_log_event_with_context(audit_logger):
    """Test event logging with context."""
    context = EventContext(
        session_id="test_session",
        request_id="test_request",
        correlation_id="test_correlation"
    )
    
    event = AuditEvent(
        type=EventType.SYSTEM_EVENT,
        source=EventSource.SERVICE,
        action="process_data",
        context=context
    )
    
    result = await audit_logger.log_event(event)
    
    # Verify context stored
    stored_event = audit_logger.storage.store.call_args[0][0]
    assert stored_event["context"]["session_id"] == "test_session"
    assert stored_event["context"]["request_id"] == "test_request"

@pytest.mark.asyncio
async def test_log_event_compliance(audit_logger):
    """Test compliance requirements in event logging."""
    # Missing required field
    event = AuditEvent(
        type=EventType.USER_ACTION,
        source=EventSource.API,
        action="login"  # Missing user_id and resource
    )
    
    with pytest.raises(ValueError) as exc:
        await audit_logger.log_event(event)
    assert "required fields" in str(exc.value).lower()
    
    # PII handling
    event = AuditEvent(
        type=EventType.USER_ACTION,
        source=EventSource.API,
        action="login",
        user_id="test_user",
        resource="auth_service",
        metadata={
            "email": "test@example.com",
            "ip_address": "192.168.1.1"
        }
    )
    
    result = await audit_logger.log_event(event)
    stored_event = audit_logger.storage.store.call_args[0][0]
    
    # PII fields should be hashed or redacted
    assert stored_event["metadata"]["email"] != "test@example.com"
    assert stored_event["metadata"]["ip_address"] != "192.168.1.1"

# Event Retrieval Tests

@pytest.mark.asyncio
async def test_get_event(audit_logger, storage_client):
    """Test event retrieval."""
    event_data = {
        "event_id": "test_id",
        "type": EventType.USER_ACTION.value,
        "timestamp": datetime.utcnow().isoformat()
    }
    storage_client.get.return_value = event_data
    
    result = await audit_logger.get_event("test_id")
    
    assert result["event_id"] == "test_id"
    assert result["type"] == EventType.USER_ACTION.value

@pytest.mark.asyncio
async def test_search_events(audit_logger, storage_client):
    """Test event searching."""
    filters = AuditFilter(
        start_time=datetime.utcnow() - timedelta(days=1),
        end_time=datetime.utcnow(),
        event_types={EventType.USER_ACTION},
        user_id="test_user"
    )
    
    events = [
        {
            "event_id": f"id_{i}",
            "type": EventType.USER_ACTION.value,
            "user_id": "test_user"
        }
        for i in range(3)
    ]
    storage_client.search.return_value = events
    
    results = await audit_logger.search_events(filters)
    
    assert len(results) == 3
    assert all(e["user_id"] == "test_user" for e in results)
    
    # Verify search parameters
    search_args = storage_client.search.call_args[1]
    assert "start_time" in search_args
    assert "event_types" in search_args
    assert "user_id" in search_args

# Retention Tests

@pytest.mark.asyncio
async def test_retention_policy(audit_logger):
    """Test retention policy enforcement."""
    # Regular event
    regular_event = AuditEvent(
        type=EventType.USER_ACTION,
        source=EventSource.API,
        action="view_data",
        user_id="test_user",
        resource="data_service"
    )
    
    result = await audit_logger.log_event(regular_event)
    stored_event = audit_logger.storage.store.call_args[0][0]
    assert stored_event["retention_period"] == 90  # Default retention
    
    # Compliance event
    compliance_event = AuditEvent(
        type=EventType.COMPLIANCE_CHECK,
        source=EventSource.SYSTEM,
        action="data_access_check",
        user_id="test_user",
        resource="pii_data"
    )
    
    result = await audit_logger.log_event(compliance_event)
    stored_event = audit_logger.storage.store.call_args[0][0]
    assert stored_event["retention_period"] == 365  # Compliance retention
    
    # Security event
    security_event = AuditEvent(
        type=EventType.SECURITY_EVENT,
        source=EventSource.SYSTEM,
        action="failed_login",
        user_id="test_user",
        resource="auth_service"
    )
    
    result = await audit_logger.log_event(security_event)
    stored_event = audit_logger.storage.store.call_args[0][0]
    assert stored_event["retention_period"] == 730  # Security retention

# Performance Tests

@pytest.mark.asyncio
async def test_bulk_logging(audit_logger):
    """Test bulk event logging performance."""
    events = [
        AuditEvent(
            type=EventType.USER_ACTION,
            source=EventSource.API,
            action="bulk_test",
            user_id=f"user_{i}",
            resource="test_service"
        )
        for i in range(100)
    ]
    
    results = await audit_logger.log_events(events)
    
    assert len(results) == 100
    assert all("event_id" in r for r in results)
    
    # Verify batch processing
    assert audit_logger.storage.store.call_count == 1  # Should use batch insert

@pytest.mark.asyncio
async def test_performance_metrics(audit_logger):
    """Test performance metric collection."""
    await audit_logger.log_event(
        AuditEvent(
            type=EventType.USER_ACTION,
            source=EventSource.API,
            action="test",
            user_id="test_user",
            resource="test_service"
        )
    )
    
    # Verify timing metrics
    audit_logger.metrics.timing.assert_called_with(
        "audit_event_processing_time",
        mock.ANY,
        tags={"type": EventType.USER_ACTION.value}
    )

# Security Tests

@pytest.mark.asyncio
async def test_event_integrity(audit_logger):
    """Test event integrity protection."""
    event = AuditEvent(
        type=EventType.SECURITY_EVENT,
        source=EventSource.SYSTEM,
        action="sensitive_action",
        user_id="test_user",
        resource="secure_service"
    )
    
    result = await audit_logger.log_event(event)
    stored_event = audit_logger.storage.store.call_args[0][0]
    
    # Should include integrity hash
    assert "integrity_hash" in stored_event
    
    # Hash should include all critical fields
    critical_fields = {
        "type", "source", "action", "user_id",
        "resource", "timestamp"
    }
    assert all(f in stored_event["integrity_hash_fields"] for f in critical_fields)

@pytest.mark.asyncio
async def test_sensitive_data_handling(audit_logger):
    """Test sensitive data handling."""
    event = AuditEvent(
        type=EventType.USER_ACTION,
        source=EventSource.API,
        action="update_profile",
        user_id="test_user",
        resource="user_service",
        metadata={
            "email": "test@example.com",
            "password": "secret123",
            "credit_card": "4111-1111-1111-1111",
            "ip_address": "192.168.1.1"
        }
    )
    
    result = await audit_logger.log_event(event)
    stored_event = audit_logger.storage.store.call_args[0][0]
    
    # Sensitive fields should be protected
    assert stored_event["metadata"]["password"] == "[REDACTED]"
    assert stored_event["metadata"]["credit_card"] == "[REDACTED]"
    assert stored_event["metadata"]["email"] != "test@example.com"  # Should be hashed
    assert stored_event["metadata"]["ip_address"] != "192.168.1.1"  # Should be hashed 