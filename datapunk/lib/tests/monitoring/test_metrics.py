import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.monitoring.metrics import (
    MetricsCollector,
    MetricsConfig,
    MetricType,
    MetricValue,
    AggregationType
)
from datapunk.lib.tracing import TracingManager

@pytest.fixture
def metrics_config():
    return MetricsConfig(
        name="test_metrics",
        flush_interval=10,  # seconds
        batch_size=100,
        retention_days=7,
        aggregation_interval=60,  # 1 minute
        default_labels={
            "environment": "test",
            "service": "metrics_test"
        }
    )

@pytest.fixture
def mock_tracing():
    return MagicMock(spec=TracingManager)

@pytest.fixture
def mock_storage():
    return AsyncMock()

@pytest.fixture
async def metrics_collector(metrics_config, mock_tracing, mock_storage):
    collector = MetricsCollector(metrics_config, mock_tracing)
    collector.storage = mock_storage
    await collector.initialize()
    return collector

@pytest.mark.asyncio
async def test_collector_initialization(metrics_collector, metrics_config):
    """Test metrics collector initialization"""
    assert metrics_collector.config == metrics_config
    assert not metrics_collector.is_stopped
    assert len(metrics_collector.metrics) == 0

@pytest.mark.asyncio
async def test_counter_metrics(metrics_collector):
    """Test counter metric collection"""
    # Record counter values
    metric_name = "requests_total"
    labels = {"endpoint": "/api/test"}
    
    await metrics_collector.increment(metric_name, labels)
    await metrics_collector.increment(metric_name, labels, value=5)
    
    # Get current value
    value = await metrics_collector.get_metric_value(metric_name, labels)
    assert value == 6
    
    # Verify storage
    metrics_collector.storage.store_metric.assert_called_with(
        metric_name,
        MetricType.COUNTER,
        6,
        labels,
        ANY  # timestamp
    )

@pytest.mark.asyncio
async def test_gauge_metrics(metrics_collector):
    """Test gauge metric collection"""
    # Record gauge values
    metric_name = "cpu_usage"
    labels = {"cpu": "0"}
    
    await metrics_collector.gauge(metric_name, 50.0, labels)
    await metrics_collector.gauge(metric_name, 75.0, labels)
    
    # Get current value
    value = await metrics_collector.get_metric_value(metric_name, labels)
    assert value == 75.0
    
    # Verify storage
    metrics_collector.storage.store_metric.assert_called_with(
        metric_name,
        MetricType.GAUGE,
        75.0,
        labels,
        ANY  # timestamp
    )

@pytest.mark.asyncio
async def test_histogram_metrics(metrics_collector):
    """Test histogram metric collection"""
    # Record histogram values
    metric_name = "request_duration_seconds"
    labels = {"endpoint": "/api/test"}
    values = [0.1, 0.2, 0.3, 0.4, 0.5]
    
    for value in values:
        await metrics_collector.histogram(metric_name, labels, value=value)
    
    # Get histogram stats
    stats = await metrics_collector.get_histogram_stats(metric_name, labels)
    
    assert stats.count == len(values)
    assert stats.sum == sum(values)
    assert stats.min == min(values)
    assert stats.max == max(values)
    assert len(stats.buckets) > 0

@pytest.mark.asyncio
async def test_summary_metrics(metrics_collector):
    """Test summary metric collection"""
    # Record summary values
    metric_name = "request_size_bytes"
    labels = {"endpoint": "/api/test"}
    values = [100, 200, 300, 400, 500]
    
    for value in values:
        await metrics_collector.summary(metric_name, labels, value=value)
    
    # Get summary stats
    stats = await metrics_collector.get_summary_stats(metric_name, labels)
    
    assert stats.count == len(values)
    assert stats.sum == sum(values)
    assert stats.quantiles[0.5] == 300  # median
    assert stats.quantiles[0.95] >= 475  # 95th percentile

@pytest.mark.asyncio
async def test_metric_aggregation(metrics_collector):
    """Test metric aggregation"""
    metric_name = "throughput"
    labels = {"service": "api"}
    
    # Record values over time
    times = [
        datetime.now() - timedelta(minutes=5),
        datetime.now() - timedelta(minutes=4),
        datetime.now() - timedelta(minutes=3)
    ]
    values = [100, 200, 300]
    
    for time, value in zip(times, values):
        await metrics_collector.gauge(metric_name, value, labels, timestamp=time)
    
    # Get aggregated values
    aggregated = await metrics_collector.get_aggregated_values(
        metric_name,
        labels,
        AggregationType.AVG,
        timedelta(minutes=5)
    )
    
    assert len(aggregated) > 0
    assert sum(v.value for v in aggregated) / len(aggregated) == 200  # average

@pytest.mark.asyncio
async def test_metric_labels(metrics_collector):
    """Test metric label handling"""
    metric_name = "requests_total"
    
    # Record metrics with different labels
    labels1 = {"endpoint": "/api/v1"}
    labels2 = {"endpoint": "/api/v2"}
    
    await metrics_collector.increment(metric_name, labels1)
    await metrics_collector.increment(metric_name, labels2)
    
    # Get values for different labels
    value1 = await metrics_collector.get_metric_value(metric_name, labels1)
    value2 = await metrics_collector.get_metric_value(metric_name, labels2)
    
    assert value1 == 1
    assert value2 == 1
    
    # Verify default labels are included
    metrics_collector.storage.store_metric.assert_any_call(
        metric_name,
        MetricType.COUNTER,
        1,
        {**labels1, **metrics_collector.config.default_labels},
        ANY  # timestamp
    )

@pytest.mark.asyncio
async def test_metric_retention(metrics_collector):
    """Test metric retention"""
    metric_name = "old_metric"
    labels = {"type": "test"}
    
    # Record old metric
    old_time = datetime.now() - timedelta(days=10)
    await metrics_collector.gauge(metric_name, 100, labels, timestamp=old_time)
    
    # Clean up old metrics
    await metrics_collector.cleanup_old_metrics()
    
    # Verify cleanup
    metrics_collector.storage.delete_metrics.assert_called_with(
        older_than=ANY  # retention threshold
    )

@pytest.mark.asyncio
async def test_metric_batch_processing(metrics_collector):
    """Test metric batch processing"""
    metric_name = "batch_metric"
    labels = {"batch": "test"}
    
    # Record multiple metrics
    for i in range(metrics_collector.config.batch_size + 1):
        await metrics_collector.increment(metric_name, labels)
    
    # Verify batch flush
    assert metrics_collector.storage.store_metrics_batch.called
    batch = metrics_collector.storage.store_metrics_batch.call_args[0][0]
    assert len(batch) == metrics_collector.config.batch_size

@pytest.mark.asyncio
async def test_error_handling(metrics_collector):
    """Test error handling"""
    # Test invalid metric type
    with pytest.raises(ValueError):
        await metrics_collector.record_metric(
            "invalid_metric",
            "INVALID_TYPE",
            1.0,
            {}
        )
    
    # Test invalid label type
    with pytest.raises(ValueError):
        await metrics_collector.increment(
            "test_metric",
            {"invalid_label": object()}
        )

@pytest.mark.asyncio
async def test_metric_export(metrics_collector):
    """Test metric export functionality"""
    # Record some metrics
    await metrics_collector.increment("requests_total", {"endpoint": "/api"})
    await metrics_collector.gauge("cpu_usage", 75.0, {"cpu": "0"})
    
    # Export metrics
    exported = await metrics_collector.export_metrics()
    
    assert len(exported) == 2
    assert any(m.name == "requests_total" for m in exported)
    assert any(m.name == "cpu_usage" for m in exported)

@pytest.mark.asyncio
async def test_tracing_integration(metrics_collector):
    """Test tracing integration"""
    # Record metric with tracing
    metric_name = "traced_metric"
    labels = {"trace": "test"}
    value = 42.0
    
    await metrics_collector.gauge(metric_name, value, labels)
    
    # Verify tracing attributes
    metrics_collector.tracing.set_attribute.assert_any_call(
        'metric.name', metric_name
    )
    metrics_collector.tracing.set_attribute.assert_any_call(
        'metric.value', value
    )
    metrics_collector.tracing.set_attribute.assert_any_call(
        'metric.type', MetricType.GAUGE.value
    ) 