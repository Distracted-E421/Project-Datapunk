import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import json
from datapunk_shared.mesh.health import (
    HealthReporter,
    ReportConfig,
    ReportFormat,
    ReportDelivery,
    ReportingError
)

@pytest.fixture
def report_config():
    return ReportConfig(
        report_interval=300,  # 5 minutes
        formats=[ReportFormat.JSON, ReportFormat.HTML],
        delivery_methods=["email", "slack"],
        retention_days=30
    )

@pytest.fixture
def health_reporter(report_config):
    return HealthReporter(config=report_config)

@pytest.fixture
def sample_health_data():
    return {
        "service1": {
            "status": "healthy",
            "uptime": 3600,
            "last_check": datetime.utcnow(),
            "checks": [
                {"name": "api", "status": "healthy"},
                {"name": "db", "status": "healthy"}
            ]
        },
        "service2": {
            "status": "degraded",
            "uptime": 1800,
            "last_check": datetime.utcnow(),
            "checks": [
                {"name": "api", "status": "healthy"},
                {"name": "cache", "status": "unhealthy"}
            ]
        }
    }

@pytest.mark.asyncio
async def test_report_generation(health_reporter, sample_health_data):
    report = await health_reporter.generate_report(sample_health_data)
    
    assert "timestamp" in report
    assert "services" in report
    assert len(report["services"]) == 2
    assert "summary" in report

@pytest.mark.asyncio
async def test_report_formatting():
    reporter = HealthReporter(
        ReportConfig(formats=[ReportFormat.JSON, ReportFormat.HTML])
    )
    
    data = {"service": {"status": "healthy"}}
    
    json_report = await reporter.format_report(data, ReportFormat.JSON)
    assert isinstance(json_report, str)
    assert json.loads(json_report)  # Valid JSON
    
    html_report = await reporter.format_report(data, ReportFormat.HTML)
    assert "<html" in html_report.lower()
    assert "</html>" in html_report.lower()

@pytest.mark.asyncio
async def test_report_delivery(health_reporter):
    with patch.object(health_reporter, '_deliver_email') as mock_email:
        with patch.object(health_reporter, '_deliver_slack') as mock_slack:
            report_data = {"status": "all healthy"}
            
            await health_reporter.deliver_report(report_data)
            
            mock_email.assert_called_once()
            mock_slack.assert_called_once()

@pytest.mark.asyncio
async def test_report_scheduling(health_reporter):
    with patch.object(health_reporter, 'generate_and_deliver') as mock_generate:
        await health_reporter.start_scheduled_reporting()
        await asyncio.sleep(0.1)  # Allow first schedule to run
        await health_reporter.stop_scheduled_reporting()
        
        assert mock_generate.called

@pytest.mark.asyncio
async def test_report_templates(health_reporter):
    # Test custom template rendering
    template = """
    Service Status Report
    {% for service in services %}
    - {{ service.name }}: {{ service.status }}
    {% endfor %}
    """
    
    health_reporter.register_template("custom", template)
    
    data = {
        "services": [
            {"name": "service1", "status": "healthy"},
            {"name": "service2", "status": "degraded"}
        ]
    }
    
    report = await health_reporter.render_template("custom", data)
    assert "Service Status Report" in report
    assert "service1: healthy" in report
    assert "service2: degraded" in report

@pytest.mark.asyncio
async def test_report_aggregation(health_reporter, sample_health_data):
    # Test data aggregation for reporting
    aggregated = await health_reporter.aggregate_data(sample_health_data)
    
    assert "total_services" in aggregated
    assert aggregated["total_services"] == 2
    assert "healthy_services" in aggregated
    assert "degraded_services" in aggregated

@pytest.mark.asyncio
async def test_report_filtering(health_reporter, sample_health_data):
    # Test report data filtering
    filters = {
        "status": "degraded",
        "min_uptime": 1000
    }
    
    filtered_data = await health_reporter.filter_data(sample_health_data, filters)
    assert len(filtered_data) == 1
    assert "service2" in filtered_data

@pytest.mark.asyncio
async def test_report_persistence(health_reporter):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        report_data = {"timestamp": datetime.utcnow(), "data": "test"}
        await health_reporter.save_report(report_data)
        
        mock_file.write.assert_called_once()

@pytest.mark.asyncio
async def test_report_cleanup(health_reporter):
    with patch('pathlib.Path.glob') as mock_glob:
        mock_glob.return_value = [
            Mock(stat=lambda: Mock(st_mtime=datetime.now().timestamp() - 31*24*3600))
        ]
        
        await health_reporter.cleanup_old_reports()
        assert mock_glob.called

@pytest.mark.asyncio
async def test_report_error_handling(health_reporter):
    with patch.object(health_reporter, '_deliver_email', side_effect=Exception("Delivery failed")):
        with pytest.raises(ReportingError):
            await health_reporter.deliver_report({"test": "data"})

@pytest.mark.asyncio
async def test_custom_report_formatter(health_reporter):
    def custom_formatter(data):
        return f"Status: {data.get('status', 'unknown')}"
    
    health_reporter.register_formatter("custom", custom_formatter)
    
    formatted = await health_reporter.format_report(
        {"status": "healthy"},
        "custom"
    )
    
    assert formatted == "Status: healthy"

@pytest.mark.asyncio
async def test_report_metrics(health_reporter, sample_health_data):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        await health_reporter.generate_report(sample_health_data)
        
        mock_collector.return_value.record_gauge.assert_called()
        mock_collector.return_value.record_histogram.assert_called()

@pytest.mark.asyncio
async def test_incremental_reporting(health_reporter):
    # Test incremental report updates
    initial_data = {"service1": {"status": "healthy"}}
    await health_reporter.update_report(initial_data)
    
    update_data = {"service2": {"status": "degraded"}}
    await health_reporter.update_report(update_data)
    
    full_report = await health_reporter.get_current_report()
    assert "service1" in full_report
    assert "service2" in full_report 