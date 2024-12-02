"""
Audit Reporting Tests
-----------------

Tests the audit reporting system including:
- Report generation
- Template management
- Cache functionality
- Report validation
- Performance optimization
- Security controls

Run with: pytest -v test_reporting.py
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import json
import tempfile
import os

from datapunk_shared.auth.audit.reporting import (
    ReportGenerator, ReportTemplate,
    TemplateValidator, TemplateCache,
    ReportFormat, ReportConfig
)
from datapunk_shared.auth.audit.reporting.templates import (
    TemplateManager, TemplateType,
    TemplateContext, TemplateData
)

# Test Fixtures

@pytest.fixture
def template_cache():
    """Mock template cache for testing."""
    cache = AsyncMock()
    cache.get = AsyncMock()
    cache.set = AsyncMock()
    cache.invalidate = AsyncMock()
    return cache

@pytest.fixture
def storage_client():
    """Mock storage client for testing."""
    client = AsyncMock()
    client.list_events = AsyncMock()
    client.get_events = AsyncMock()
    return client

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.timing = AsyncMock()
    return client

@pytest.fixture
def report_config():
    """Create report configuration for testing."""
    return ReportConfig(
        default_format=ReportFormat.JSON,
        max_events_per_report=10000,
        enable_caching=True,
        cache_ttl=timedelta(hours=1),
        template_refresh_interval=timedelta(minutes=30)
    )

@pytest.fixture
def template_validator():
    """Create template validator for testing."""
    return TemplateValidator()

@pytest.fixture
def report_generator(storage_client, template_cache, metrics_client,
                    report_config, template_validator):
    """Create report generator for testing."""
    return ReportGenerator(
        storage=storage_client,
        template_cache=template_cache,
        metrics=metrics_client,
        config=report_config,
        validator=template_validator
    )

# Template Management Tests

@pytest.mark.asyncio
async def test_template_loading(report_generator, template_cache):
    """Test template loading and validation."""
    template_data = {
        "id": "security_report",
        "type": TemplateType.SECURITY.value,
        "version": "1.0",
        "content": {
            "title": "Security Audit Report",
            "sections": ["summary", "details", "recommendations"]
        }
    }
    template_cache.get.return_value = template_data
    
    template = await report_generator.load_template("security_report")
    
    assert template.id == "security_report"
    assert template.type == TemplateType.SECURITY
    assert "sections" in template.content

@pytest.mark.asyncio
async def test_template_validation(report_generator, template_validator):
    """Test template validation rules."""
    # Valid template
    valid_template = ReportTemplate(
        id="compliance_report",
        type=TemplateType.COMPLIANCE,
        version="1.0",
        content={
            "title": "Compliance Report",
            "sections": ["overview", "findings"],
            "required_fields": ["event_type", "timestamp"]
        }
    )
    
    assert template_validator.validate(valid_template) is True
    
    # Invalid template
    invalid_template = ReportTemplate(
        id="invalid_report",
        type=TemplateType.SECURITY,
        version="1.0",
        content={
            "title": "Invalid Report"
            # Missing required sections
        }
    )
    
    with pytest.raises(ValueError) as exc:
        template_validator.validate(invalid_template)
    assert "required sections" in str(exc.value).lower()

@pytest.mark.asyncio
async def test_template_caching(report_generator, template_cache):
    """Test template caching behavior."""
    template_id = "performance_report"
    
    # First load - should hit storage
    await report_generator.load_template(template_id)
    template_cache.get.assert_called_once_with(template_id)
    
    # Second load - should hit cache
    template_cache.get.reset_mock()
    await report_generator.load_template(template_id)
    template_cache.get.assert_called_once_with(template_id)
    
    # Template update - should invalidate cache
    await report_generator.update_template(template_id, {"new": "content"})
    template_cache.invalidate.assert_called_once_with(template_id)

# Report Generation Tests

@pytest.mark.asyncio
async def test_generate_report(report_generator, storage_client):
    """Test report generation process."""
    # Setup test events
    events = [
        {
            "event_id": f"id_{i}",
            "type": "security_event",
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "high" if i % 2 == 0 else "medium"
        }
        for i in range(10)
    ]
    storage_client.get_events.return_value = events
    
    # Generate report
    report = await report_generator.generate_report(
        template_id="security_report",
        start_time=datetime.utcnow() - timedelta(days=1),
        end_time=datetime.utcnow()
    )
    
    assert report["total_events"] == 10
    assert "high_severity_events" in report["summary"]
    assert "medium_severity_events" in report["summary"]

@pytest.mark.asyncio
async def test_report_formats(report_generator):
    """Test different report output formats."""
    events = [
        {
            "event_id": f"id_{i}",
            "type": "audit_event",
            "timestamp": datetime.utcnow().isoformat()
        }
        for i in range(5)
    ]
    
    # JSON format
    json_report = await report_generator.generate_report(
        template_id="basic_report",
        format=ReportFormat.JSON,
        events=events
    )
    assert isinstance(json_report, dict)
    
    # CSV format
    csv_report = await report_generator.generate_report(
        template_id="basic_report",
        format=ReportFormat.CSV,
        events=events
    )
    assert isinstance(csv_report, str)
    assert "event_id,type,timestamp" in csv_report
    
    # PDF format
    pdf_report = await report_generator.generate_report(
        template_id="basic_report",
        format=ReportFormat.PDF,
        events=events
    )
    assert isinstance(pdf_report, bytes)

@pytest.mark.asyncio
async def test_report_aggregation(report_generator):
    """Test report data aggregation."""
    events = [
        {
            "event_id": f"id_{i}",
            "type": "access_event",
            "user_id": f"user_{i % 3}",  # Create user patterns
            "resource": f"resource_{i % 2}",
            "timestamp": datetime.utcnow().isoformat()
        }
        for i in range(100)
    ]
    
    report = await report_generator.generate_report(
        template_id="access_report",
        events=events,
        aggregations=["user_id", "resource"]
    )
    
    # Verify aggregations
    assert "user_access_counts" in report
    assert "resource_access_counts" in report
    assert len(report["user_access_counts"]) == 3  # Unique users
    assert len(report["resource_access_counts"]) == 2  # Unique resources

# Performance Tests

@pytest.mark.asyncio
async def test_large_report_handling(report_generator, storage_client):
    """Test handling of large reports."""
    # Setup large number of events
    events = [
        {
            "event_id": f"id_{i}",
            "type": "test_event",
            "timestamp": datetime.utcnow().isoformat()
        }
        for i in range(15000)  # Exceeds max_events_per_report
    ]
    storage_client.get_events.return_value = events
    
    # Should handle gracefully with pagination
    report = await report_generator.generate_report(
        template_id="large_report",
        start_time=datetime.utcnow() - timedelta(days=1),
        end_time=datetime.utcnow()
    )
    
    assert report["is_paginated"] is True
    assert report["total_pages"] > 1
    assert len(report["events"]) <= 10000  # Respects max_events_per_report

@pytest.mark.asyncio
async def test_concurrent_report_generation(report_generator):
    """Test concurrent report generation."""
    import asyncio
    
    # Generate multiple reports concurrently
    reports = await asyncio.gather(*[
        report_generator.generate_report(
            template_id="concurrent_test",
            start_time=datetime.utcnow() - timedelta(days=1),
            end_time=datetime.utcnow()
        )
        for _ in range(5)
    ])
    
    assert len(reports) == 5
    assert all(isinstance(r, dict) for r in reports)

# Security Tests

@pytest.mark.asyncio
async def test_template_security(report_generator, template_validator):
    """Test template security controls."""
    # Template with potential security issues
    unsafe_template = ReportTemplate(
        id="unsafe_report",
        type=TemplateType.CUSTOM,
        version="1.0",
        content={
            "title": "Unsafe Report",
            "query": "DELETE FROM events",  # Unsafe SQL
            "script": "os.system('rm -rf /')"  # Unsafe command
        }
    )
    
    with pytest.raises(SecurityError) as exc:
        template_validator.validate(unsafe_template)
    assert "security violation" in str(exc.value).lower()

@pytest.mark.asyncio
async def test_data_filtering(report_generator):
    """Test sensitive data filtering in reports."""
    events = [
        {
            "event_id": f"id_{i}",
            "type": "user_event",
            "user_data": {
                "email": "test@example.com",
                "password_hash": "abc123",
                "credit_card": "4111-1111-1111-1111"
            }
        }
        for i in range(5)
    ]
    
    report = await report_generator.generate_report(
        template_id="user_report",
        events=events,
        redact_sensitive=True
    )
    
    # Verify sensitive data is redacted
    assert "[REDACTED]" in str(report)
    assert "4111-1111-1111-1111" not in str(report)
    assert "password_hash" not in str(report)

# Error Handling Tests

@pytest.mark.asyncio
async def test_template_error_handling(report_generator):
    """Test handling of template errors."""
    # Missing template
    with pytest.raises(TemplateNotFoundError):
        await report_generator.load_template("nonexistent_template")
    
    # Invalid template version
    with pytest.raises(TemplateVersionError):
        await report_generator.load_template("incompatible_version")
    
    # Template rendering error
    with pytest.raises(TemplateRenderError):
        await report_generator.generate_report(
            template_id="broken_template",
            events=[{"invalid": "data"}]
        )

@pytest.mark.asyncio
async def test_data_validation(report_generator):
    """Test input data validation."""
    # Invalid date range
    with pytest.raises(ValueError):
        await report_generator.generate_report(
            template_id="test_report",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() - timedelta(days=1)  # End before start
        )
    
    # Invalid event data
    with pytest.raises(ValueError):
        await report_generator.generate_report(
            template_id="test_report",
            events=[{"timestamp": "invalid_date"}]  # Invalid timestamp
        ) 