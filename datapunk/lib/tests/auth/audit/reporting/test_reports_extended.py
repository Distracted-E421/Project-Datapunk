"""
Extended Reports Tests
------------------

Tests the extended reporting functionality including:
- Advanced report generation
- Custom formatting
- Data visualization
- Interactive features
- Export options
- Security controls

Run with: pytest -v test_reports_extended.py
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import json

from datapunk_shared.auth.audit.reporting.audit_reports_extended import (
    ExtendedReportGenerator,
    ExtendedReportFormat,
    ExtendedTemplateManager
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
def visualization_client():
    """Mock visualization client for testing."""
    client = AsyncMock()
    client.create_chart = AsyncMock()
    client.create_dashboard = AsyncMock()
    return client

@pytest.fixture
def report_generator(storage_client, template_manager,
                    metrics_client, visualization_client):
    """Create extended report generator for testing."""
    return ExtendedReportGenerator(
        storage=storage_client,
        templates=template_manager,
        metrics=metrics_client,
        visualization=visualization_client
    )

@pytest.fixture
def event_data():
    """Create event data for testing."""
    return [
        {
            "event_id": f"id_{i}",
            "event_type": "test_event",
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "high" if i % 2 == 0 else "low",
            "metrics": {
                "duration": i * 100,
                "size": i * 1000
            }
        }
        for i in range(10)
    ]

# Advanced Report Generation Tests

@pytest.mark.asyncio
async def test_interactive_report(report_generator, event_data):
    """Test interactive report generation."""
    report_generator.storage.get_events.return_value = event_data
    
    report = await report_generator.generate_interactive_report(
        template_id="interactive_report",
        data=event_data,
        features={
            "filtering": True,
            "sorting": True,
            "drill_down": True
        }
    )
    
    assert "interactive_elements" in report
    assert report["interactive_elements"]["filtering"] is True
    assert report["interactive_elements"]["sorting"] is True
    assert report["interactive_elements"]["drill_down"] is True

@pytest.mark.asyncio
async def test_dashboard_generation(report_generator, event_data):
    """Test dashboard report generation."""
    report_generator.storage.get_events.return_value = event_data
    
    dashboard = await report_generator.generate_dashboard(
        template_id="dashboard_template",
        data=event_data,
        layout={
            "widgets": [
                {"type": "chart", "position": {"x": 0, "y": 0}},
                {"type": "metrics", "position": {"x": 1, "y": 0}}
            ]
        }
    )
    
    assert "widgets" in dashboard
    assert len(dashboard["widgets"]) == 2
    assert dashboard["layout"] is not None

# Data Visualization Tests

@pytest.mark.asyncio
async def test_chart_generation(report_generator, event_data):
    """Test chart generation in reports."""
    report_generator.storage.get_events.return_value = event_data
    
    # Time series chart
    time_chart = await report_generator.create_visualization(
        data=event_data,
        type="time_series",
        options={
            "x_field": "timestamp",
            "y_field": "metrics.duration",
            "aggregation": "avg"
        }
    )
    
    assert time_chart["type"] == "time_series"
    assert "data_points" in time_chart
    assert len(time_chart["data_points"]) > 0
    
    # Distribution chart
    dist_chart = await report_generator.create_visualization(
        data=event_data,
        type="distribution",
        options={
            "field": "severity",
            "chart_type": "pie"
        }
    )
    
    assert dist_chart["type"] == "distribution"
    assert dist_chart["data"]["high"] == 5
    assert dist_chart["data"]["low"] == 5

@pytest.mark.asyncio
async def test_metric_widgets(report_generator, event_data):
    """Test metric widget generation."""
    report_generator.storage.get_events.return_value = event_data
    
    metrics = await report_generator.create_metric_widgets(
        data=event_data,
        metrics=[
            {
                "name": "Average Duration",
                "field": "metrics.duration",
                "aggregation": "avg"
            },
            {
                "name": "Total Size",
                "field": "metrics.size",
                "aggregation": "sum"
            }
        ]
    )
    
    assert len(metrics) == 2
    assert metrics[0]["value"] > 0
    assert metrics[1]["value"] > 0

# Export Options Tests

@pytest.mark.asyncio
async def test_export_formats(report_generator, event_data):
    """Test various export formats."""
    report_generator.storage.get_events.return_value = event_data
    
    # Excel export
    excel_report = await report_generator.export_report(
        template_id="export_template",
        format=ExtendedReportFormat.EXCEL,
        data=event_data
    )
    assert isinstance(excel_report, bytes)
    
    # PowerPoint export
    ppt_report = await report_generator.export_report(
        template_id="export_template",
        format=ExtendedReportFormat.POWERPOINT,
        data=event_data
    )
    assert isinstance(ppt_report, bytes)
    
    # HTML export
    html_report = await report_generator.export_report(
        template_id="export_template",
        format=ExtendedReportFormat.HTML,
        data=event_data
    )
    assert isinstance(html_report, str)
    assert "<html" in html_report

@pytest.mark.asyncio
async def test_custom_export_options(report_generator, event_data):
    """Test custom export options."""
    report_generator.storage.get_events.return_value = event_data
    
    report = await report_generator.export_report(
        template_id="custom_export",
        format=ExtendedReportFormat.EXCEL,
        options={
            "sheets": ["Summary", "Details", "Charts"],
            "password_protected": True,
            "include_metadata": True
        }
    )
    
    assert isinstance(report, bytes)
    report_generator.metrics.increment.assert_called_with(
        "report_exports",
        tags={"format": "excel", "protected": True}
    )

# Interactive Features Tests

@pytest.mark.asyncio
async def test_drill_down_functionality(report_generator, event_data):
    """Test drill-down functionality in reports."""
    report_generator.storage.get_events.return_value = event_data
    
    report = await report_generator.generate_interactive_report(
        template_id="drill_down_report",
        data=event_data,
        drill_down_config={
            "dimensions": ["severity", "event_type"],
            "metrics": ["duration", "size"],
            "max_depth": 3
        }
    )
    
    assert "drill_down_data" in report
    assert len(report["drill_down_data"]["dimensions"]) == 2
    assert report["drill_down_data"]["max_depth"] == 3

@pytest.mark.asyncio
async def test_filtering_capabilities(report_generator, event_data):
    """Test filtering capabilities in reports."""
    report_generator.storage.get_events.return_value = event_data
    
    report = await report_generator.generate_interactive_report(
        template_id="filter_report",
        data=event_data,
        filter_config={
            "fields": ["severity", "event_type"],
            "operators": ["equals", "contains", "greater_than"],
            "default_filters": [
                {"field": "severity", "operator": "equals", "value": "high"}
            ]
        }
    )
    
    assert "filter_config" in report
    assert len(report["filter_config"]["fields"]) == 2
    assert len(report["filtered_data"]) == 5  # High severity events

# Security Tests

@pytest.mark.asyncio
async def test_report_access_control(report_generator, event_data):
    """Test report access control."""
    report = await report_generator.generate_interactive_report(
        template_id="secure_report",
        data=event_data,
        security_config={
            "access_level": "confidential",
            "allowed_roles": ["admin", "auditor"],
            "redact_fields": ["ip_address", "user_id"]
        }
    )
    
    assert "security" in report
    assert report["security"]["access_level"] == "confidential"
    assert "ip_address" not in str(report["data"])

@pytest.mark.asyncio
async def test_export_security(report_generator, event_data):
    """Test security controls for exports."""
    with pytest.raises(ValueError) as exc:
        await report_generator.export_report(
            template_id="secure_report",
            format=ExtendedReportFormat.EXCEL,
            data=event_data,
            security_config={
                "access_level": "restricted",
                "allowed_roles": ["admin"]
            },
            user_role="viewer"  # Insufficient permissions
        )
    assert "permission" in str(exc.value).lower()

# Performance Tests

@pytest.mark.asyncio
async def test_large_interactive_report(report_generator):
    """Test performance with large interactive reports."""
    # Generate large dataset
    large_data = [
        {
            "event_id": f"id_{i}",
            "event_type": "test_event",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {"value": i}
        }
        for i in range(10000)
    ]
    report_generator.storage.get_events.return_value = large_data
    
    report = await report_generator.generate_interactive_report(
        template_id="large_report",
        data=large_data,
        performance_config={
            "pagination": True,
            "page_size": 100,
            "lazy_loading": True
        }
    )
    
    assert report["is_paginated"] is True
    assert report["page_size"] == 100
    assert "total_pages" in report

@pytest.mark.asyncio
async def test_visualization_performance(report_generator, event_data):
    """Test visualization performance optimization."""
    report_generator.storage.get_events.return_value = event_data
    
    dashboard = await report_generator.generate_dashboard(
        template_id="performance_dashboard",
        data=event_data,
        optimization_config={
            "data_sampling": True,
            "sample_size": 1000,
            "cache_charts": True
        }
    )
    
    assert "optimization" in dashboard
    assert dashboard["optimization"]["data_sampling"] is True
    report_generator.metrics.timing.assert_called_with(
        "dashboard_generation_time",
        mock.ANY,
        tags={"optimized": True}
    ) 