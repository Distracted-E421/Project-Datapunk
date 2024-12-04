import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.health import (
    HealthMetrics,
    MetricsConfig,
    MetricType,
    MetricValue,
    AggregationType,
    MetricReport
)

@pytest.fixture
def metrics_config():
    return MetricsConfig(
        collection_interval=5,  # seconds
        retention_period=3600,  # 1 hour
        batch_size=100,
        enable_persistence=True
    )

@pytest.fixture
def health_metrics(metrics_config):
    return HealthMetrics(config=metrics_config)

@pytest.fixture
def sample_metrics():
    return [
        {
            "name": "response_time",
            "type": MetricType.GAUGE,
            "value": 100.0,
            "tags": {"endpoint": "/api/test"}
        },
        {
            "name": "request_count",
            "type": MetricType.COUNTER,
            "value": 1.0,
            "tags": {"method": "GET"}
        }
    ]

@pytest.mark.asyncio
async def test_metrics_initialization(health_metrics, metrics_config):
    assert health_metrics.config == metrics_config
    assert health_metrics.is_initialized
    assert len(health_metrics.collectors) == 0

@pytest.mark.asyncio
async def test_metric_registration(health_metrics):
    await health_metrics.register_metric(
        name="response_time",
        type=MetricType.GAUGE,
        description="API response time in milliseconds",
        unit="ms"
    )
    
    assert "response_time" in health_metrics.metrics
    metric = health_metrics.metrics["response_time"]
    assert metric.type == MetricType.GAUGE
    assert metric.unit == "ms"

@pytest.mark.asyncio
async def test_metric_collection(health_metrics, sample_metrics):
    for metric in sample_metrics:
        await health_metrics.register_metric(
            name=metric["name"],
            type=metric["type"]
        )
        await health_metrics.record_metric(
            name=metric["name"],
            value=metric["value"],
            tags=metric["tags"]
        )
    
    collected = await health_metrics.get_metrics()
    assert len(collected) == len(sample_metrics)
    assert all(m["name"] in [sm["name"] for sm in sample_metrics] 
              for m in collected)

@pytest.mark.asyncio
async def test_counter_metrics(health_metrics):
    await health_metrics.register_metric(
        name="requests",
        type=MetricType.COUNTER,
        description="Total request count"
    )
    
    # Increment counter multiple times
    for _ in range(5):
        await health_metrics.increment_counter(
            name="requests",
            tags={"endpoint": "/api"}
        )
    
    value = await health_metrics.get_metric_value(
        name="requests",
        tags={"endpoint": "/api"}
    )
    assert value == 5

@pytest.mark.asyncio
async def test_gauge_metrics(health_metrics):
    await health_metrics.register_metric(
        name="memory_usage",
        type=MetricType.GAUGE,
        description="Memory usage in MB",
        unit="MB"
    )
    
    # Set gauge value
    await health_metrics.set_gauge(
        name="memory_usage",
        value=1024.5,
        tags={"server": "app1"}
    )
    
    value = await health_metrics.get_metric_value(
        name="memory_usage",
        tags={"server": "app1"}
    )
    assert abs(value - 1024.5) < 0.01

@pytest.mark.asyncio
async def test_histogram_metrics(health_metrics):
    await health_metrics.register_metric(
        name="response_times",
        type=MetricType.HISTOGRAM,
        description="Response time distribution",
        unit="ms"
    )
    
    # Record multiple values
    values = [10, 20, 30, 40, 50]
    for value in values:
        await health_metrics.record_histogram(
            name="response_times",
            value=value,
            tags={"endpoint": "/api"}
        )
    
    histogram = await health_metrics.get_histogram(
        name="response_times",
        tags={"endpoint": "/api"}
    )
    
    assert histogram.count == len(values)
    assert histogram.sum == sum(values)
    assert 10 <= histogram.min <= histogram.max <= 50

@pytest.mark.asyncio
async def test_metric_aggregation(health_metrics):
    await health_metrics.register_metric(
        name="cpu_usage",
        type=MetricType.GAUGE,
        description="CPU usage percentage"
    )
    
    # Record values over time
    base_time = datetime.utcnow()
    values = [20, 30, 40, 50, 60]
    
    for i, value in enumerate(values):
        await health_metrics.record_metric(
            name="cpu_usage",
            value=value,
            timestamp=base_time + timedelta(seconds=i),
            tags={"server": "app1"}
        )
    
    # Test different aggregations
    aggregations = {
        AggregationType.AVG: 40.0,
        AggregationType.MAX: 60.0,
        AggregationType.MIN: 20.0,
        AggregationType.SUM: 200.0
    }
    
    for agg_type, expected in aggregations.items():
        result = await health_metrics.aggregate_metric(
            name="cpu_usage",
            aggregation=agg_type,
            tags={"server": "app1"}
        )
        assert abs(result - expected) < 0.01

@pytest.mark.asyncio
async def test_metric_tagging(health_metrics):
    await health_metrics.register_metric(
        name="errors",
        type=MetricType.COUNTER,
        description="Error count by type"
    )
    
    # Record metrics with different tags
    tags_list = [
        {"type": "validation", "severity": "warning"},
        {"type": "validation", "severity": "error"},
        {"type": "system", "severity": "error"}
    ]
    
    for tags in tags_list:
        await health_metrics.increment_counter(
            name="errors",
            tags=tags
        )
    
    # Query by tag combinations
    validation_errors = await health_metrics.get_metrics_by_tags(
        name="errors",
        tags={"type": "validation"}
    )
    assert len(validation_errors) == 2
    
    severe_errors = await health_metrics.get_metrics_by_tags(
        name="errors",
        tags={"severity": "error"}
    )
    assert len(severe_errors) == 2

@pytest.mark.asyncio
async def test_metric_persistence(health_metrics):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        # Record some metrics
        await health_metrics.register_metric(
            name="test_metric",
            type=MetricType.GAUGE
        )
        await health_metrics.record_metric(
            name="test_metric",
            value=100.0
        )
        
        await health_metrics.save_state()
        mock_file.write.assert_called_once()
        
        await health_metrics.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_metric_reporting(health_metrics):
    # Register and record some metrics
    await health_metrics.register_metric(
        name="system_metrics",
        type=MetricType.GAUGE,
        description="System metrics"
    )
    
    metrics = {
        "cpu": 75.5,
        "memory": 1024.0,
        "disk": 500.0
    }
    
    for name, value in metrics.items():
        await health_metrics.record_metric(
            name="system_metrics",
            value=value,
            tags={"type": name}
        )
    
    report = await health_metrics.generate_report()
    assert isinstance(report, MetricReport)
    assert len(report.metrics) == len(metrics)

@pytest.mark.asyncio
async def test_metric_cleanup(health_metrics):
    await health_metrics.register_metric(
        name="old_metric",
        type=MetricType.GAUGE
    )
    
    # Record metric with old timestamp
    old_time = datetime.utcnow() - timedelta(hours=2)
    await health_metrics.record_metric(
        name="old_metric",
        value=100.0,
        timestamp=old_time
    )
    
    # Run cleanup
    await health_metrics.cleanup()
    
    # Verify old metrics are removed
    value = await health_metrics.get_metric_value("old_metric")
    assert value is None

@pytest.mark.asyncio
async def test_metric_rate_calculation(health_metrics):
    await health_metrics.register_metric(
        name="requests_per_second",
        type=MetricType.COUNTER,
        description="Request rate"
    )
    
    # Record requests over time
    base_time = datetime.utcnow()
    for i in range(50):
        await health_metrics.increment_counter(
            name="requests_per_second",
            timestamp=base_time + timedelta(seconds=i/10)  # 10 requests per second
        )
    
    rate = await health_metrics.calculate_rate(
        name="requests_per_second",
        window_size=1.0  # 1 second window
    )
    
    assert abs(rate - 10.0) < 1.0  # Allow small deviation

@pytest.mark.asyncio
async def test_metric_alerts(health_metrics):
    alerts = []
    
    def alert_handler(metric_name, value, threshold):
        alerts.append((metric_name, value, threshold))
    
    await health_metrics.register_metric(
        name="error_rate",
        type=MetricType.GAUGE,
        description="Error rate percentage"
    )
    
    # Configure alert threshold
    await health_metrics.set_alert_threshold(
        name="error_rate",
        threshold=5.0,
        handler=alert_handler
    )
    
    # Record value exceeding threshold
    await health_metrics.record_metric(
        name="error_rate",
        value=7.5
    )
    
    assert len(alerts) == 1
    assert alerts[0][0] == "error_rate"
    assert alerts[0][1] == 7.5
    assert alerts[0][2] == 5.0 