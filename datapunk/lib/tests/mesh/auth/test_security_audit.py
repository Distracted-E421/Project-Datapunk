import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json
from datapunk_shared.mesh.auth import (
    SecurityAudit,
    AuditConfig,
    AuditEvent,
    AuditTrail,
    ComplianceReport
)

@pytest.fixture
def audit_config():
    return AuditConfig(
        retention_days=90,
        log_level="INFO",
        compliance_standards=["SOC2", "HIPAA"],
        audit_trail_format="json"
    )

@pytest.fixture
def security_audit(audit_config):
    return SecurityAudit(config=audit_config)

@pytest.fixture
def sample_audit_events():
    return [
        AuditEvent(
            event_type="user_access",
            user_id="user123",
            resource_id="api/endpoint",
            action="GET",
            timestamp=datetime.utcnow(),
            status="success",
            details={"ip": "192.168.1.100"}
        ),
        AuditEvent(
            event_type="config_change",
            user_id="admin456",
            resource_id="security_settings",
            action="UPDATE",
            timestamp=datetime.utcnow(),
            status="success",
            details={"changes": {"timeout": 300}}
        )
    ]

@pytest.mark.asyncio
async def test_audit_initialization(security_audit, audit_config):
    assert security_audit.config == audit_config
    assert security_audit.is_initialized
    assert len(security_audit.audit_trail) == 0

@pytest.mark.asyncio
async def test_event_logging(security_audit, sample_audit_events):
    for event in sample_audit_events:
        await security_audit.log_event(event)
    
    assert len(security_audit.audit_trail) == len(sample_audit_events)
    assert all(e.event_type in ["user_access", "config_change"] 
              for e in security_audit.audit_trail)

@pytest.mark.asyncio
async def test_audit_trail_generation(security_audit, sample_audit_events):
    # Log multiple events
    for event in sample_audit_events:
        await security_audit.log_event(event)
    
    # Generate audit trail
    trail = await security_audit.generate_audit_trail(
        start_time=datetime.utcnow() - timedelta(hours=1)
    )
    
    assert isinstance(trail, AuditTrail)
    assert len(trail.events) == len(sample_audit_events)
    assert trail.format == "json"

@pytest.mark.asyncio
async def test_compliance_reporting(security_audit, sample_audit_events):
    # Log events
    for event in sample_audit_events:
        await security_audit.log_event(event)
    
    # Generate compliance report
    report = await security_audit.generate_compliance_report(
        standard="SOC2",
        start_time=datetime.utcnow() - timedelta(days=30)
    )
    
    assert isinstance(report, ComplianceReport)
    assert report.standard == "SOC2"
    assert len(report.findings) > 0

@pytest.mark.asyncio
async def test_audit_retention(security_audit):
    # Create old events
    old_event = AuditEvent(
        event_type="user_access",
        user_id="user123",
        resource_id="api/endpoint",
        action="GET",
        timestamp=datetime.utcnow() - timedelta(days=100),  # Older than retention
        status="success",
        details={"ip": "192.168.1.100"}
    )
    
    await security_audit.log_event(old_event)
    
    # Run retention cleanup
    await security_audit.cleanup_old_events()
    
    assert len(security_audit.audit_trail) == 0

@pytest.mark.asyncio
async def test_audit_search(security_audit, sample_audit_events):
    # Log events
    for event in sample_audit_events:
        await security_audit.log_event(event)
    
    # Search for specific events
    results = await security_audit.search_events(
        criteria={
            "event_type": "user_access",
            "user_id": "user123"
        }
    )
    
    assert len(results) == 1
    assert results[0].event_type == "user_access"
    assert results[0].user_id == "user123"

@pytest.mark.asyncio
async def test_audit_export(security_audit, sample_audit_events):
    # Log events
    for event in sample_audit_events:
        await security_audit.log_event(event)
    
    # Export audit data
    exported = await security_audit.export_audit_data(
        format="json",
        start_time=datetime.utcnow() - timedelta(hours=1)
    )
    
    assert isinstance(exported, str)
    data = json.loads(exported)
    assert len(data["events"]) == len(sample_audit_events)

@pytest.mark.asyncio
async def test_concurrent_logging(security_audit):
    # Generate multiple events
    events = [
        AuditEvent(
            event_type="user_access",
            user_id=f"user{i}",
            resource_id="api/endpoint",
            action="GET",
            timestamp=datetime.utcnow(),
            status="success",
            details={"ip": f"192.168.1.{i}"}
        )
        for i in range(100)
    ]
    
    # Log events concurrently
    await asyncio.gather(*[
        security_audit.log_event(event)
        for event in events
    ])
    
    assert len(security_audit.audit_trail) == 100

@pytest.mark.asyncio
async def test_audit_persistence(security_audit):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        # Save audit state
        await security_audit.save_state()
        mock_file.write.assert_called_once()
        
        # Load audit state
        await security_audit.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_compliance_check(security_audit, sample_audit_events):
    # Log events
    for event in sample_audit_events:
        await security_audit.log_event(event)
    
    # Run compliance check
    compliance_status = await security_audit.check_compliance(
        standard="SOC2",
        requirements=["access_logging", "change_tracking"]
    )
    
    assert isinstance(compliance_status, dict)
    assert "access_logging" in compliance_status
    assert "change_tracking" in compliance_status
    assert all(isinstance(v, bool) for v in compliance_status.values())

@pytest.mark.asyncio
async def test_audit_summary(security_audit, sample_audit_events):
    # Log events
    for event in sample_audit_events:
        await security_audit.log_event(event)
    
    # Generate summary
    summary = await security_audit.generate_summary(
        start_time=datetime.utcnow() - timedelta(hours=1)
    )
    
    assert "total_events" in summary
    assert "event_types" in summary
    assert "unique_users" in summary
    assert summary["total_events"] == len(sample_audit_events)

@pytest.mark.asyncio
async def test_audit_metrics(security_audit, sample_audit_events):
    # Log events
    for event in sample_audit_events:
        await security_audit.log_event(event)
    
    # Calculate metrics
    metrics = await security_audit.calculate_metrics(
        start_time=datetime.utcnow() - timedelta(hours=1)
    )
    
    assert "events_per_type" in metrics
    assert "events_per_user" in metrics
    assert "success_rate" in metrics

@pytest.mark.asyncio
async def test_audit_filtering(security_audit, sample_audit_events):
    # Log events
    for event in sample_audit_events:
        await security_audit.log_event(event)
    
    # Filter events
    filtered = await security_audit.filter_events(
        filters={
            "status": "success",
            "action": "GET"
        }
    )
    
    assert len(filtered) == 1
    assert filtered[0].status == "success"
    assert filtered[0].action == "GET"

@pytest.mark.asyncio
async def test_compliance_report_generation(security_audit):
    with patch.object(security_audit, '_generate_compliance_data') as mock_generate:
        mock_generate.return_value = {
            "controls": {"access_control": True, "encryption": True},
            "violations": [],
            "recommendations": []
        }
        
        report = await security_audit.generate_compliance_report("SOC2")
        
        assert report.standard == "SOC2"
        assert "controls" in report.data
        assert "violations" in report.data
        mock_generate.assert_called_once_with("SOC2") 