"""
Compliance Manager Tests
--------------------

Tests the compliance manager functionality including:
- Standard management
- Event validation
- Report generation
- Metric tracking
- Performance monitoring
- Error handling

Run with: pytest -v test_manager.py
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import json

from datapunk_shared.auth.audit.compliance.manager import (
    ComplianceManager,
    ComplianceCheck,
    ComplianceReport,
    ComplianceStatus
)
from datapunk_shared.auth.audit.compliance.standards import (
    ComplianceStandard,
    StandardType,
    ValidationRule,
    RequirementLevel,
    ComplianceRule
)

# Test Fixtures

@pytest.fixture
def storage_client():
    """Mock storage client for testing."""
    client = AsyncMock()
    client.get_events = AsyncMock()
    client.store_report = AsyncMock()
    return client

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.gauge = AsyncMock()
    client.timing = AsyncMock()
    return client

@pytest.fixture
def notification_client():
    """Mock notification client for testing."""
    client = AsyncMock()
    client.send = AsyncMock()
    return client

@pytest.fixture
def compliance_standard():
    """Create compliance standard for testing."""
    return ComplianceStandard(
        id="SOC2",
        name="SOC 2",
        version="2022",
        requirements=[
            ComplianceRule(
                id="ACC-1",
                name="Access Control",
                level=RequirementLevel.REQUIRED,
                validation_rules=[
                    ValidationRule(
                        field="access_type",
                        condition="in",
                        values=["read", "write", "admin"]
                    )
                ]
            ),
            ComplianceRule(
                id="LOG-1",
                name="Audit Logging",
                level=RequirementLevel.REQUIRED,
                validation_rules=[
                    ValidationRule(
                        field="event_type",
                        condition="exists",
                        values=None
                    )
                ]
            )
        ]
    )

@pytest.fixture
def compliance_manager(storage_client, metrics_client,
                      notification_client, compliance_standard):
    """Create compliance manager for testing."""
    return ComplianceManager(
        storage=storage_client,
        metrics=metrics_client,
        notifications=notification_client,
        standards=[compliance_standard]
    )

# Standard Management Tests

@pytest.mark.asyncio
async def test_standard_registration(compliance_manager, compliance_standard):
    """Test standard registration."""
    # Register new standard
    new_standard = ComplianceStandard(
        id="HIPAA",
        name="HIPAA",
        version="2022",
        requirements=[]
    )
    await compliance_manager.register_standard(new_standard)
    
    # Verify standard registered
    assert new_standard.id in compliance_manager.standards
    assert compliance_manager.get_standard("HIPAA") == new_standard
    
    # Verify metrics
    compliance_manager.metrics.increment.assert_called_with(
        "standards_registered",
        tags={"standard": "HIPAA"}
    )

@pytest.mark.asyncio
async def test_standard_updates(compliance_manager):
    """Test standard update handling."""
    # Create updated version
    updated_standard = ComplianceStandard(
        id="SOC2",
        name="SOC 2",
        version="2023",  # New version
        requirements=[]
    )
    
    await compliance_manager.update_standard(updated_standard)
    
    # Verify update
    current = compliance_manager.get_standard("SOC2")
    assert current.version == "2023"
    
    # Verify notification
    compliance_manager.notifications.send.assert_called_with(
        type="standard_updated",
        details={"standard": "SOC2", "version": "2023"}
    )

# Event Validation Tests

@pytest.mark.asyncio
async def test_event_validation(compliance_manager):
    """Test event validation against standards."""
    event = {
        "event_id": "test_1",
        "access_type": "read",
        "event_type": "data_access",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    result = await compliance_manager.validate_event(
        event=event,
        standard_id="SOC2"
    )
    
    assert result.is_compliant is True
    assert result.standard_id == "SOC2"
    assert len(result.validations) == 2  # Two rules checked

@pytest.mark.asyncio
async def test_bulk_validation(compliance_manager, storage_client):
    """Test bulk event validation."""
    events = [
        {
            "event_id": f"id_{i}",
            "access_type": "read",
            "event_type": "data_access",
            "timestamp": datetime.utcnow().isoformat()
        }
        for i in range(100)
    ]
    storage_client.get_events.return_value = events
    
    results = await compliance_manager.validate_events(
        events=events,
        standard_id="SOC2"
    )
    
    assert len(results) == 100
    assert all(r.is_compliant for r in results)
    
    # Verify performance metrics
    compliance_manager.metrics.timing.assert_called_with(
        "bulk_validation_time",
        mock.ANY,
        tags={"count": 100}
    )

# Report Generation Tests

@pytest.mark.asyncio
async def test_compliance_report_generation(compliance_manager, storage_client):
    """Test compliance report generation."""
    # Setup test events
    events = [
        {
            "event_id": f"id_{i}",
            "access_type": "read" if i % 2 == 0 else "invalid",
            "event_type": "data_access",
            "timestamp": datetime.utcnow().isoformat()
        }
        for i in range(10)
    ]
    storage_client.get_events.return_value = events
    
    report = await compliance_manager.generate_report(
        standard_id="SOC2",
        start_time=datetime.utcnow() - timedelta(days=1),
        end_time=datetime.utcnow()
    )
    
    assert isinstance(report, ComplianceReport)
    assert report.total_events == 10
    assert report.compliant_events == 5
    assert report.non_compliant_events == 5
    assert "access_type" in report.violation_reasons

@pytest.mark.asyncio
async def test_report_aggregation(compliance_manager):
    """Test report aggregation functionality."""
    reports = [
        ComplianceReport(
            standard_id="SOC2",
            total_events=100,
            compliant_events=80,
            non_compliant_events=20,
            start_time=datetime.utcnow() - timedelta(days=1),
            end_time=datetime.utcnow()
        ),
        ComplianceReport(
            standard_id="SOC2",
            total_events=100,
            compliant_events=90,
            non_compliant_events=10,
            start_time=datetime.utcnow() - timedelta(days=2),
            end_time=datetime.utcnow() - timedelta(days=1)
        )
    ]
    
    aggregated = await compliance_manager.aggregate_reports(reports)
    
    assert aggregated.total_events == 200
    assert aggregated.compliant_events == 170
    assert aggregated.non_compliant_events == 30
    assert aggregated.compliance_rate == 0.85

# Performance Tests

@pytest.mark.asyncio
async def test_concurrent_validation(compliance_manager):
    """Test concurrent validation processing."""
    import asyncio
    
    # Generate multiple validation tasks
    events = [
        {
            "event_id": f"id_{i}",
            "access_type": "read",
            "event_type": "data_access"
        }
        for i in range(50)
    ]
    
    # Run validations concurrently
    results = await asyncio.gather(*[
        compliance_manager.validate_event(event, "SOC2")
        for event in events
    ])
    
    assert len(results) == 50
    assert all(r.is_compliant for r in results)

@pytest.mark.asyncio
async def test_performance_monitoring(compliance_manager):
    """Test performance monitoring."""
    event = {
        "event_id": "test",
        "access_type": "read",
        "event_type": "data_access"
    }
    
    await compliance_manager.validate_event(event, "SOC2")
    
    # Verify timing metrics
    compliance_manager.metrics.timing.assert_called_with(
        "validation_time",
        mock.ANY,
        tags={"standard": "SOC2"}
    )

# Error Handling Tests

@pytest.mark.asyncio
async def test_standard_not_found(compliance_manager):
    """Test handling of unknown standards."""
    event = {"id": "test"}
    
    with pytest.raises(ValueError) as exc:
        await compliance_manager.validate_event(
            event=event,
            standard_id="UNKNOWN"
        )
    assert "standard not found" in str(exc.value).lower()

@pytest.mark.asyncio
async def test_invalid_event_data(compliance_manager):
    """Test handling of invalid event data."""
    # Invalid timestamp
    event = {
        "event_id": "test",
        "access_type": "read",
        "event_type": "test",
        "timestamp": "invalid_date"
    }
    
    with pytest.raises(ValueError) as exc:
        await compliance_manager.validate_event(
            event=event,
            standard_id="SOC2"
        )
    assert "invalid timestamp" in str(exc.value).lower()

@pytest.mark.asyncio
async def test_storage_failures(compliance_manager, storage_client):
    """Test handling of storage failures."""
    storage_client.get_events.side_effect = Exception("Storage error")
    
    with pytest.raises(Exception) as exc:
        await compliance_manager.generate_report(
            standard_id="SOC2",
            start_time=datetime.utcnow() - timedelta(days=1),
            end_time=datetime.utcnow()
        )
    assert "storage error" in str(exc.value).lower()

# Security Tests

@pytest.mark.asyncio
async def test_sensitive_data_handling(compliance_manager):
    """Test handling of sensitive data."""
    event = {
        "event_id": "test",
        "access_type": "read",
        "event_type": "user_data_access",
        "user_data": {
            "ssn": "123-45-6789",
            "credit_card": "4111-1111-1111-1111"
        }
    }
    
    result = await compliance_manager.validate_event(
        event=event,
        standard_id="SOC2"
    )
    
    # Verify sensitive data not logged
    assert "ssn" not in str(result)
    assert "credit_card" not in str(result)

@pytest.mark.asyncio
async def test_critical_violations(compliance_manager, notification_client):
    """Test handling of critical compliance violations."""
    event = {
        "event_id": "test",
        "access_type": "invalid",
        "event_type": "security_critical",
        "severity": "high"
    }
    
    await compliance_manager.validate_event(
        event=event,
        standard_id="SOC2"
    )
    
    # Verify critical violation notification
    notification_client.send.assert_called_with(
        type="compliance_violation",
        severity="high",
        details=mock.ANY
    ) 