"""
Report Generator Tests
------------------

Tests the report generation functionality including:
- Report creation and formatting
- Data aggregation
- Template integration
- Performance optimization
- Error handling
- Output formats

Run with: pytest -v test_generator.py
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import json

from datapunk_shared.auth.audit.reporting.generator import (
    ReportGenerator,
    ReportFormat,
    ReportConfig,
    ReportOptions
)
from datapunk_shared.auth.audit.reporting.templates import (
    TemplateType,
    TemplateContext,
    TemplateData
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
def template_manager():
    """Mock template manager for testing."""
    manager = AsyncMock()
    manager.load_template = AsyncMock()
    manager.render_template = AsyncMock()
    return manager

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
        max_events_per_report=1000,
        enable_caching=True,
        template_refresh_interval=timedelta(minutes=30)
    )

@pytest.fixture
def report_generator(storage_client, template_manager,
                    metrics_client, report_config):
    """Create report generator for testing."""
    return ReportGenerator(
        storage=storage_client,
        templates=template_manager,
        metrics=metrics_client,
        config=report_config
    )

@pytest.fixture
def template_data():
    """Create template data for testing."""
    return TemplateData(
        id="audit_report",
        type=TemplateType.AUDIT,
        version="1.0",
        content={
            "sections": ["summary", "details"],
            "fields": {
                "event_type": {"type": "string", "required": True},
                "timestamp": {"type": "datetime", "required": True}
            }
        }
    )

@pytest.fixture
def event_data():
    """Create event data for testing."""
    return [
        {
            "event_id": f"id_{i}",
            "event_type": "test_event",
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "high" if i % 2 == 0 else "low"
        }
        for i in range(10)
    ]

# Report Generation Tests

@pytest.mark.asyncio
async def test_generate_report(report_generator, template_data, event_data):
    """Test basic report generation."""
    # Setup mocks
    report_generator.storage.get_events.return_value = event_data
    report_generator.templates.load_template.return_value = template_data
    report_generator.templates.render_template.return_value = {
        "summary": "Test Report",
        "details": event_data
    }
    
    report = await report_generator.generate_report(
        template_id="audit_report",
        start_time=datetime.utcnow() - timedelta(days=1),
        end_time=datetime.utcnow()
    )
    
    assert report is not None
    assert "summary" in report
    assert "details" in report
    assert len(report["details"]) == 10

@pytest.mark.asyncio
async def test_report_formats(report_generator, template_data, event_data):
    """Test different report output formats."""
    report_generator.storage.get_events.return_value = event_data
    report_generator.templates.load_template.return_value = template_data
    
    # JSON format
    json_report = await report_generator.generate_report(
        template_id="audit_report",
        format=ReportFormat.JSON
    )
    assert isinstance(json_report, dict)
    
    # CSV format
    report_generator.templates.render_template.return_value = event_data
    csv_report = await report_generator.generate_report(
        template_id="audit_report",
        format=ReportFormat.CSV
    )
    assert isinstance(csv_report, str)
    assert "event_id,event_type,timestamp" in csv_report
    
    # PDF format
    pdf_report = await report_generator.generate_report(
        template_id="audit_report",
        format=ReportFormat.PDF
    )
    assert isinstance(pdf_report, bytes)

# Data Aggregation Tests

@pytest.mark.asyncio
async def test_data_aggregation(report_generator, event_data):
    """Test data aggregation in reports."""
    report_generator.storage.get_events.return_value = event_data
    
    report = await report_generator.generate_report(
        template_id="audit_report",
        aggregations=["severity"]
    )
    
    assert "aggregations" in report
    assert report["aggregations"]["severity"] == {
        "high": 5,
        "low": 5
    }

@pytest.mark.asyncio
async def test_time_based_aggregation(report_generator):
    """Test time-based data aggregation."""
    # Create time series data
    events = [
        {
            "event_id": f"id_{i}",
            "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
            "value": i
        }
        for i in range(24)  # 24 hours of data
    ]
    report_generator.storage.get_events.return_value = events
    
    report = await report_generator.generate_report(
        template_id="audit_report",
        aggregations=["hourly_count"]
    )
    
    assert "time_series" in report
    assert len(report["time_series"]["hourly"]) == 24

# Template Integration Tests

@pytest.mark.asyncio
async def test_template_integration(report_generator, template_data):
    """Test template integration in reports."""
    report_generator.templates.load_template.return_value = template_data
    
    # Custom template content
    template_data.content["formatting"] = {
        "date_format": "%Y-%m-%d",
        "number_format": "%.2f"
    }
    
    data = {
        "timestamp": datetime.utcnow(),
        "value": 123.456
    }
    
    report = await report_generator.generate_report(
        template_id="audit_report",
        data=data
    )
    
    # Verify formatting applied
    assert datetime.utcnow().strftime("%Y-%m-%d") in str(report)
    assert "123.46" in str(report)

@pytest.mark.asyncio
async def test_template_variables(report_generator, template_data):
    """Test template variable substitution."""
    template_data.content["variables"] = {
        "title": "Audit Report for ${period}",
        "footer": "Generated by ${user}"
    }
    report_generator.templates.load_template.return_value = template_data
    
    report = await report_generator.generate_report(
        template_id="audit_report",
        variables={
            "period": "January 2024",
            "user": "test_user"
        }
    )
    
    assert "January 2024" in str(report)
    assert "test_user" in str(report)

# Performance Tests

@pytest.mark.asyncio
async def test_large_report_handling(report_generator, event_data):
    """Test handling of large reports."""
    # Create large dataset
    large_data = event_data * 200  # 2000 events
    report_generator.storage.get_events.return_value = large_data
    
    report = await report_generator.generate_report(
        template_id="audit_report"
    )
    
    assert report["is_paginated"] is True
    assert report["total_pages"] > 1
    assert len(report["events"]) <= 1000  # Respects max_events_per_report

@pytest.mark.asyncio
async def test_concurrent_generation(report_generator):
    """Test concurrent report generation."""
    import asyncio
    
    # Generate multiple reports concurrently
    reports = await asyncio.gather(*[
        report_generator.generate_report(
            template_id="audit_report",
            start_time=datetime.utcnow() - timedelta(days=1),
            end_time=datetime.utcnow()
        )
        for _ in range(5)
    ])
    
    assert len(reports) == 5
    assert all(isinstance(r, dict) for r in reports)

# Error Handling Tests

@pytest.mark.asyncio
async def test_invalid_template(report_generator):
    """Test handling of invalid templates."""
    report_generator.templates.load_template.side_effect = ValueError("Template not found")
    
    with pytest.raises(ValueError) as exc:
        await report_generator.generate_report(
            template_id="nonexistent"
        )
    assert "template not found" in str(exc.value).lower()

@pytest.mark.asyncio
async def test_invalid_date_range(report_generator):
    """Test handling of invalid date ranges."""
    with pytest.raises(ValueError) as exc:
        await report_generator.generate_report(
            template_id="audit_report",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() - timedelta(days=1)  # End before start
        )
    assert "date range" in str(exc.value).lower()

@pytest.mark.asyncio
async def test_data_validation(report_generator, template_data):
    """Test data validation in reports."""
    report_generator.templates.load_template.return_value = template_data
    
    # Invalid data
    invalid_data = [
        {
            "event_id": "test",
            "timestamp": "invalid_date"  # Invalid timestamp
        }
    ]
    report_generator.storage.get_events.return_value = invalid_data
    
    with pytest.raises(ValueError) as exc:
        await report_generator.generate_report(
            template_id="audit_report"
        )
    assert "invalid" in str(exc.value).lower()

# Output Format Tests

@pytest.mark.asyncio
async def test_json_formatting(report_generator, event_data):
    """Test JSON output formatting."""
    report_generator.storage.get_events.return_value = event_data
    
    report = await report_generator.generate_report(
        template_id="audit_report",
        format=ReportFormat.JSON,
        formatting_options={"pretty": True}
    )
    
    # Verify JSON structure
    assert isinstance(report, dict)
    json_str = json.dumps(report, indent=2)
    assert json_str.count("\n") > 10  # Pretty printed

@pytest.mark.asyncio
async def test_csv_formatting(report_generator, event_data):
    """Test CSV output formatting."""
    report_generator.storage.get_events.return_value = event_data
    
    report = await report_generator.generate_report(
        template_id="audit_report",
        format=ReportFormat.CSV,
        formatting_options={
            "delimiter": "|",
            "headers": True
        }
    )
    
    assert isinstance(report, str)
    assert "|" in report
    assert report.startswith("event_id|event_type|timestamp")

@pytest.mark.asyncio
async def test_pdf_formatting(report_generator, event_data):
    """Test PDF output formatting."""
    report_generator.storage.get_events.return_value = event_data
    
    report = await report_generator.generate_report(
        template_id="audit_report",
        format=ReportFormat.PDF,
        formatting_options={
            "page_size": "A4",
            "orientation": "portrait"
        }
    )
    
    assert isinstance(report, bytes)
    assert report.startswith(b"%PDF") 