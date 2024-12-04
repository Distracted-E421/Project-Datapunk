import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh import (
    DiscoveryMetrics,
    MetricsConfig,
    ServiceMetric,
    MetricType,
    MetricsError
)

@pytest.fixture
def metrics_config():
    return MetricsConfig(
        collection_interval=1.0,
        retention_period=3600,  # 1 hour
        batch_size=100,
        aggregation_window=60  # 1 minute
    )

@pytest.fixture
def discovery_metrics(metrics_config):
    return DiscoveryMetrics(config=metrics_config)

@pytest.fixture
def sample_metrics():
    return [
        ServiceMetric(
            service="test-service",
            metric_type=MetricType.COUNTER,
            name="requests_total",
            value=100,
            timestamp=datetime.utcnow()
        ),
        ServiceMetric(
            service="test-service",
            metric_type=MetricType.GAUGE,
            name="active_connections",
            value=50,
            timestamp=datetime.utcnow()
        ),
        ServiceMetric(
            service="test-service",
            metric_type=MetricType.HISTOGRAM,
            name="response_time",
            value=0.2,
            timestamp=datetime.utcnow()
        )
    ]

@pytest.mark.asyncio
async def test_metrics_initialization(discovery_metrics, metrics_config):
    assert discovery_metrics.config == metrics_config
    assert len(discovery_metrics.metrics) == 0
    assert not discovery_metrics.is_collecting

@pytest.mark.asyncio
async def test_metric_collection(discovery_metrics, sample_metrics):
    # Record metrics
    for metric in sample_metrics:
        await discovery_metrics.record_metric(metric)
    
    # Verify collection
    collected = discovery_metrics.get_metrics("test-service")
    assert len(collected) == 3
    assert any(m.name == "requests_total" for m in collected)

@pytest.mark.asyncio
async def test_metric_aggregation(discovery_metrics):
    # Record multiple values for same metric
    base_time = datetime.utcnow()
    values = [10, 20, 30, 40, 50]
    
    for i, value in enumerate(values):
        metric = ServiceMetric(
            service="test-service",
            metric_type=MetricType.COUNTER,
            name="test_counter",
            value=value,
            timestamp=base_time + timedelta(seconds=i)
        )
        await discovery_metrics.record_metric(metric)
    
    # Aggregate metrics
    aggregated = await discovery_metrics.aggregate_metrics(
        service="test-service",
        metric_name="test_counter",
        window=timedelta(seconds=5)
    )
    
    assert aggregated.total == sum(values)
    assert aggregated.average == sum(values) / len(values)

@pytest.mark.asyncio
async def test_metric_types(discovery_metrics):
    # Test counter
    counter = ServiceMetric(
        service="test-service",
        metric_type=MetricType.COUNTER,
        name="counter_metric",
        value=1
    )
    await discovery_metrics.record_metric(counter)
    await discovery_metrics.record_metric(counter)  # Should accumulate
    
    # Test gauge
    gauge = ServiceMetric(
        service="test-service",
        metric_type=MetricType.GAUGE,
        name="gauge_metric",
        value=50
    )
    await discovery_metrics.record_metric(gauge)
    
    # Test histogram
    histogram = ServiceMetric(
        service="test-service",
        metric_type=MetricType.HISTOGRAM,
        name="histogram_metric",
        value=0.5
    )
    await discovery_metrics.record_metric(histogram)
    
    metrics = discovery_metrics.get_metrics("test-service")
    counter_metric = next(m for m in metrics if m.name == "counter_metric")
    gauge_metric = next(m for m in metrics if m.name == "gauge_metric")
    histogram_metric = next(m for m in metrics if m.name == "histogram_metric")
    
    assert counter_metric.value == 2  # Accumulated value
    assert gauge_metric.value == 50  # Last value
    assert histogram_metric.value == 0.5  # Single observation

@pytest.mark.asyncio
async def test_metric_retention(discovery_metrics):
    # Create metric with old timestamp
    old_metric = ServiceMetric(
        service="test-service",
        metric_type=MetricType.COUNTER,
        name="old_metric",
        value=100,
        timestamp=datetime.utcnow() - timedelta(hours=2)
    )
    
    await discovery_metrics.record_metric(old_metric)
    
    # Cleanup old metrics
    await discovery_metrics.cleanup_old_metrics()
    
    metrics = discovery_metrics.get_metrics("test-service")
    assert len(metrics) == 0

@pytest.mark.asyncio
async def test_metric_persistence(discovery_metrics, sample_metrics):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        # Record metrics
        for metric in sample_metrics:
            await discovery_metrics.record_metric(metric)
        
        await discovery_metrics.save_metrics()
        mock_file.write.assert_called_once()
        
        await discovery_metrics.load_metrics()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_metric_reporting(discovery_metrics, sample_metrics):
    reported_metrics = []
    
    async def mock_reporter(metrics):
        reported_metrics.extend(metrics)
    
    discovery_metrics.register_reporter(mock_reporter)
    
    # Record metrics
    for metric in sample_metrics:
        await discovery_metrics.record_metric(metric)
    
    # Trigger reporting
    await discovery_metrics.report_metrics()
    
    assert len(reported_metrics) == len(sample_metrics)

@pytest.mark.asyncio
async def test_concurrent_recording(discovery_metrics):
    # Create multiple recording tasks
    tasks = []
    for i in range(10):
        metric = ServiceMetric(
            service="test-service",
            metric_type=MetricType.COUNTER,
            name="concurrent_metric",
            value=1
        )
        tasks.append(discovery_metrics.record_metric(metric))
    
    # Execute concurrently
    await asyncio.gather(*tasks)
    
    metrics = discovery_metrics.get_metrics("test-service")
    concurrent_metric = next(m for m in metrics if m.name == "concurrent_metric")
    assert concurrent_metric.value == 10

@pytest.mark.asyncio
async def test_metric_filtering(discovery_metrics, sample_metrics):
    # Record metrics
    for metric in sample_metrics:
        await discovery_metrics.record_metric(metric)
    
    # Filter metrics
    filtered = discovery_metrics.filter_metrics(
        lambda m: m.metric_type == MetricType.COUNTER
    )
    
    assert len(filtered) == 1
    assert filtered[0].name == "requests_total"

@pytest.mark.asyncio
async def test_metric_aggregation_functions(discovery_metrics):
    # Record values for testing different aggregation functions
    values = [10, 20, 30, 40, 50]
    
    for value in values:
        metric = ServiceMetric(
            service="test-service",
            metric_type=MetricType.GAUGE,
            name="test_metric",
            value=value
        )
        await discovery_metrics.record_metric(metric)
    
    stats = await discovery_metrics.calculate_statistics(
        service="test-service",
        metric_name="test_metric"
    )
    
    assert stats.min == 10
    assert stats.max == 50
    assert stats.average == 30
    assert stats.median == 30
    assert stats.percentile_95 == 50

@pytest.mark.asyncio
async def test_metric_tagging(discovery_metrics):
    # Record metrics with tags
    metric = ServiceMetric(
        service="test-service",
        metric_type=MetricType.COUNTER,
        name="tagged_metric",
        value=100,
        tags={"environment": "test", "region": "us-west"}
    )
    
    await discovery_metrics.record_metric(metric)
    
    # Query by tags
    filtered = discovery_metrics.get_metrics_by_tags(
        tags={"environment": "test"}
    )
    
    assert len(filtered) == 1
    assert filtered[0].name == "tagged_metric"

@pytest.mark.asyncio
async def test_metric_alerts(discovery_metrics):
    alerts = []
    
    def alert_handler(metric, threshold):
        alerts.append((metric, threshold))
    
    # Register alert
    discovery_metrics.register_alert(
        metric_name="test_metric",
        threshold=100,
        handler=alert_handler
    )
    
    # Record metric that exceeds threshold
    metric = ServiceMetric(
        service="test-service",
        metric_type=MetricType.GAUGE,
        name="test_metric",
        value=150
    )
    
    await discovery_metrics.record_metric(metric)
    
    assert len(alerts) == 1
    assert alerts[0][1] == 100  # Threshold value

@pytest.mark.asyncio
async def test_cleanup(discovery_metrics, sample_metrics):
    cleanup_called = False
    
    async def cleanup_handler():
        nonlocal cleanup_called
        cleanup_called = True
    
    discovery_metrics.on_cleanup(cleanup_handler)
    
    # Record metrics
    for metric in sample_metrics:
        await discovery_metrics.record_metric(metric)
    
    await discovery_metrics.cleanup()
    
    assert cleanup_called
    assert len(discovery_metrics.metrics) == 0 