"""
Audit Types Tests
-------------

Tests the audit type system including:
- Event type definitions
- Type validation
- Type conversion
- Type serialization
- Error handling

Run with: pytest -v test_types.py
"""

import pytest
from datetime import datetime
from enum import Enum
import json

from datapunk_shared.auth.audit.types import (
    AuditEventType,
    AuditLevel,
    AuditContext,
    AuditMetadata,
    AuditEventID,
    AuditTimestamp,
    AuditEventStatus
)

# Type Definition Tests

def test_event_type_values():
    """Test audit event type enumeration."""
    assert AuditEventType.USER_ACTION.value == "user_action"
    assert AuditEventType.SYSTEM_EVENT.value == "system_event"
    assert AuditEventType.SECURITY_EVENT.value == "security_event"
    assert AuditEventType.COMPLIANCE_CHECK.value == "compliance_check"
    
    # Verify all types are unique
    values = [t.value for t in AuditEventType]
    assert len(values) == len(set(values))

def test_audit_level_ordering():
    """Test audit level enumeration ordering."""
    assert AuditLevel.MINIMAL < AuditLevel.BASIC
    assert AuditLevel.BASIC < AuditLevel.DETAILED
    assert AuditLevel.DETAILED < AuditLevel.DEBUG
    
    # Verify comparison operations
    assert AuditLevel.MINIMAL <= AuditLevel.BASIC
    assert AuditLevel.DEBUG >= AuditLevel.DETAILED
    assert AuditLevel.BASIC != AuditLevel.DETAILED

def test_event_status_transitions():
    """Test audit event status transitions."""
    assert AuditEventStatus.PENDING < AuditEventStatus.PROCESSING
    assert AuditEventStatus.PROCESSING < AuditEventStatus.COMPLETED
    assert AuditEventStatus.COMPLETED < AuditEventStatus.ARCHIVED
    
    # Verify invalid transitions
    assert not AuditEventStatus.ARCHIVED < AuditEventStatus.PENDING
    assert not AuditEventStatus.COMPLETED < AuditEventStatus.PROCESSING

# Context Tests

def test_audit_context_creation():
    """Test audit context creation and validation."""
    context = AuditContext(
        correlation_id="test_correlation",
        session_id="test_session",
        request_id="test_request",
        user_id="test_user",
        timestamp=datetime.utcnow()
    )
    
    assert context.correlation_id == "test_correlation"
    assert context.session_id == "test_session"
    assert context.request_id == "test_request"
    assert context.user_id == "test_user"
    assert isinstance(context.timestamp, datetime)

def test_audit_context_validation():
    """Test audit context validation."""
    # Invalid correlation ID
    with pytest.raises(ValueError):
        AuditContext(correlation_id="")
    
    # Invalid timestamp
    with pytest.raises(ValueError):
        AuditContext(
            correlation_id="test",
            timestamp="invalid_date"
        )

def test_context_serialization():
    """Test audit context serialization."""
    timestamp = datetime.utcnow()
    context = AuditContext(
        correlation_id="test_correlation",
        timestamp=timestamp
    )
    
    # Convert to dict
    data = context.to_dict()
    assert isinstance(data, dict)
    assert data["correlation_id"] == "test_correlation"
    assert data["timestamp"] == timestamp.isoformat()
    
    # Convert to JSON
    json_data = json.dumps(data)
    assert isinstance(json_data, str)
    
    # Deserialize
    loaded = AuditContext.from_dict(json.loads(json_data))
    assert loaded.correlation_id == context.correlation_id
    assert loaded.timestamp.isoformat() == timestamp.isoformat()

# Metadata Tests

def test_metadata_creation():
    """Test audit metadata creation and validation."""
    metadata = AuditMetadata(
        source="test_source",
        category="test_category",
        severity="high",
        tags=["test", "audit"],
        custom_fields={
            "field1": "value1",
            "field2": 123
        }
    )
    
    assert metadata.source == "test_source"
    assert metadata.category == "test_category"
    assert metadata.severity == "high"
    assert "test" in metadata.tags
    assert metadata.custom_fields["field1"] == "value1"

def test_metadata_validation():
    """Test metadata validation rules."""
    # Invalid source
    with pytest.raises(ValueError):
        AuditMetadata(source="")
    
    # Invalid severity
    with pytest.raises(ValueError):
        AuditMetadata(
            source="test",
            severity="invalid"
        )
    
    # Invalid tags
    with pytest.raises(ValueError):
        AuditMetadata(
            source="test",
            tags="not_a_list"
        )

def test_metadata_serialization():
    """Test metadata serialization."""
    metadata = AuditMetadata(
        source="test_source",
        category="test_category",
        severity="high",
        tags=["test"],
        custom_fields={"key": "value"}
    )
    
    # Convert to dict
    data = metadata.to_dict()
    assert isinstance(data, dict)
    assert data["source"] == "test_source"
    assert data["severity"] == "high"
    assert "test" in data["tags"]
    
    # Convert to JSON
    json_data = json.dumps(data)
    assert isinstance(json_data, str)
    
    # Deserialize
    loaded = AuditMetadata.from_dict(json.loads(json_data))
    assert loaded.source == metadata.source
    assert loaded.severity == metadata.severity
    assert loaded.tags == metadata.tags

# ID Generation Tests

def test_event_id_generation():
    """Test audit event ID generation."""
    id1 = AuditEventID.generate()
    id2 = AuditEventID.generate()
    
    # Verify uniqueness
    assert id1 != id2
    
    # Verify format
    assert len(id1) >= 32  # Should be sufficiently long
    assert isinstance(id1, str)
    assert id1.isalnum()  # Should be alphanumeric

def test_event_id_validation():
    """Test event ID validation."""
    # Valid ID
    assert AuditEventID.validate("test123") is True
    
    # Invalid IDs
    assert AuditEventID.validate("") is False
    assert AuditEventID.validate("invalid#id") is False
    assert AuditEventID.validate(None) is False

# Timestamp Tests

def test_timestamp_creation():
    """Test audit timestamp creation."""
    # Current time
    ts1 = AuditTimestamp.now()
    assert isinstance(ts1.datetime, datetime)
    
    # From datetime
    dt = datetime.utcnow()
    ts2 = AuditTimestamp(dt)
    assert ts2.datetime == dt
    
    # From ISO string
    iso = dt.isoformat()
    ts3 = AuditTimestamp.from_iso(iso)
    assert ts3.datetime.isoformat() == iso

def test_timestamp_comparison():
    """Test timestamp comparison operations."""
    ts1 = AuditTimestamp.now()
    ts2 = AuditTimestamp(ts1.datetime)
    ts3 = AuditTimestamp(datetime.utcnow())
    
    assert ts1 == ts2
    assert ts1 <= ts2
    assert ts1 >= ts2
    assert ts1 != ts3

def test_timestamp_formatting():
    """Test timestamp formatting options."""
    dt = datetime(2024, 1, 1, 12, 0, 0)
    ts = AuditTimestamp(dt)
    
    # ISO format
    assert ts.to_iso() == "2024-01-01T12:00:00"
    
    # Custom format
    assert ts.format("%Y-%m-%d") == "2024-01-01"
    assert ts.format("%H:%M:%S") == "12:00:00"

# Error Handling Tests

def test_type_conversion_errors():
    """Test type conversion error handling."""
    # Invalid datetime conversion
    with pytest.raises(ValueError):
        AuditTimestamp.from_iso("invalid_date")
    
    # Invalid context conversion
    with pytest.raises(ValueError):
        AuditContext.from_dict({"invalid": "data"})
    
    # Invalid metadata conversion
    with pytest.raises(ValueError):
        AuditMetadata.from_dict({"invalid": "data"}) 