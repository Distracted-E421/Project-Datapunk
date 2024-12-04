import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk.lib.metrics import (
    MetricsCollector,
    MetricsConfig,
    MetricType,
    MetricValue,
    MetricsError
)

@pytest.fixture
def metrics_config():
    return MetricsConfig(
        name="test_metrics",
        collectors=[
            {
                "name": "prometheus",
                "type": "prometheus",
                "port": 9090,
                "path": "/metrics"
            },
            {
                "name": "statsd",
                "type": "statsd",
                "host": "localhost",
                "port": 8125
            }
        ],
        default_labels={
            "service": "test_service",
            "environment": "test"
        },
        aggregation_interval=60,  # seconds
        buffer_size=1000
    )

@pytest.fixture
async def metrics_collector(metrics_config):
    collector = MetricsCollector(metrics_config)
    await collector.initialize()
    return collector

@pytest.mark.asyncio
async def test_collector_initialization(metrics_collector, metrics_config):
    """Test metrics collector initialization"""
    assert metrics_collector.config == metrics_config
    assert metrics_collector.is_initialized
    assert len(metrics_collector.collectors) == len(metrics_config.collectors)

@pytest.mark.asyncio
async def test_counter_metric(metrics_collector):
    """Test counter metric type"""
    # Create counter
    await metrics_collector.create_counter(
        name="test_counter",
        description="Test counter metric",
        labels=["endpoint"]
    )
    
    # Increment counter
    await metrics_collector.increment(
        "test_counter",
        labels={"endpoint": "/api/test"},
        value=1
    )
    
    # Get counter value
    value = await metrics_collector.get_metric_value("test_counter")
    assert value.type == MetricType.COUNTER
    assert value.value == 1

@pytest.mark.asyncio
async def test_gauge_metric(metrics_collector):
    """Test gauge metric type"""
    # Create gauge
    await metrics_collector.create_gauge(
        name="test_gauge",
        description="Test gauge metric",
        labels=["component"]
    )
    
    # Set gauge value
    await metrics_collector.set_gauge(
        "test_gauge",
        labels={"component": "database"},
        value=42.5
    )
    
    # Get gauge value
    value = await metrics_collector.get_metric_value("test_gauge")
    assert value.type == MetricType.GAUGE
    assert value.value == 42.5

@pytest.mark.asyncio
async def test_histogram_metric(metrics_collector):
    """Test histogram metric type"""
    # Create histogram
    await metrics_collector.create_histogram(
        name="test_histogram",
        description="Test histogram metric",
        labels=["method"],
        buckets=[0.1, 0.5, 1.0, 5.0]
    )
    
    # Record values
    values = [0.2, 0.7, 1.2, 3.5]
    for v in values:
        await metrics_collector.observe(
            "test_histogram",
            labels={"method": "GET"},
            value=v
        )
    
    # Get histogram value
    value = await metrics_collector.get_metric_value("test_histogram")
    assert value.type == MetricType.HISTOGRAM
    assert len(value.buckets) == 4
    assert value.sum == sum(values)

@pytest.mark.asyncio
async def test_summary_metric(metrics_collector):
    """Test summary metric type"""
    # Create summary
    await metrics_collector.create_summary(
        name="test_summary",
        description="Test summary metric",
        labels=["status"],
        quantiles=[0.5, 0.9, 0.99]
    )
    
    # Record values
    values = list(range(100))
    for v in values:
        await metrics_collector.observe(
            "test_summary",
            labels={"status": "success"},
            value=v
        )
    
    # Get summary value
    value = await metrics_collector.get_metric_value("test_summary")
    assert value.type == MetricType.SUMMARY
    assert len(value.quantiles) == 3
    assert value.count == len(values)

@pytest.mark.asyncio
async def test_metric_labels(metrics_collector):
    """Test metric labels"""
    # Create metric with labels
    await metrics_collector.create_counter(
        name="test_labels",
        description="Test labeled metric",
        labels=["service", "endpoint", "status"]
    )
    
    # Record values with different label combinations
    await metrics_collector.increment(
        "test_labels",
        labels={
            "service": "api",
            "endpoint": "/users",
            "status": "success"
        }
    )
    
    await metrics_collector.increment(
        "test_labels",
        labels={
            "service": "api",
            "endpoint": "/users",
            "status": "error"
        }
    )
    
    # Get values for specific labels
    success_value = await metrics_collector.get_metric_value(
        "test_labels",
        labels={"status": "success"}
    )
    error_value = await metrics_collector.get_metric_value(
        "test_labels",
        labels={"status": "error"}
    )
    
    assert success_value.value == 1
    assert error_value.value == 1

@pytest.mark.asyncio
async def test_metric_aggregation(metrics_collector):
    """Test metric aggregation"""
    await metrics_collector.create_counter(
        name="test_aggregation",
        description="Test aggregation metric"
    )
    
    # Record values over time
    start_time = datetime.now()
    for _ in range(10):
        await metrics_collector.increment("test_aggregation")
        await asyncio.sleep(0.1)
    
    # Get aggregated value
    aggregated = await metrics_collector.get_aggregated_value(
        "test_aggregation",
        start_time=start_time,
        end_time=datetime.now()
    )
    
    assert aggregated.count == 10
    assert aggregated.rate > 0

@pytest.mark.asyncio
async def test_metric_export(metrics_collector):
    """Test metric export"""
    # Create and record some metrics
    await metrics_collector.create_counter("test_export", "Test export metric")
    await metrics_collector.increment("test_export")
    
    # Export metrics
    exported = await metrics_collector.export_metrics()
    
    assert len(exported) > 0
    assert any(m["name"] == "test_export" for m in exported)
    assert all("timestamp" in m for m in exported)

@pytest.mark.asyncio
async def test_metric_reset(metrics_collector):
    """Test metric reset"""
    # Create and record metric
    await metrics_collector.create_counter("test_reset", "Test reset metric")
    await metrics_collector.increment("test_reset", value=5)
    
    # Reset metric
    await metrics_collector.reset_metric("test_reset")
    
    # Verify reset
    value = await metrics_collector.get_metric_value("test_reset")
    assert value.value == 0

@pytest.mark.asyncio
async def test_error_handling(metrics_collector):
    """Test error handling"""
    # Test with invalid metric type
    with pytest.raises(MetricsError):
        await metrics_collector.create_metric(
            name="invalid",
            type="invalid_type"
        )
    
    # Test with invalid label
    with pytest.raises(MetricsError):
        await metrics_collector.increment(
            "test_counter",
            labels={"invalid_label": "value"}
        )

@pytest.mark.asyncio
async def test_metric_persistence(metrics_collector):
    """Test metric persistence"""
    # Create persistent metric
    await metrics_collector.create_counter(
        name="test_persistence",
        description="Test persistence metric",
        persist=True
    )
    
    # Record value
    await metrics_collector.increment("test_persistence")
    
    # Save state
    await metrics_collector.save_state()
    
    # Create new collector and load state
    new_collector = MetricsCollector(metrics_collector.config)
    await new_collector.initialize()
    await new_collector.load_state()
    
    # Verify persisted value
    value = await new_collector.get_metric_value("test_persistence")
    assert value.value == 1

@pytest.mark.asyncio
async def test_batch_operations(metrics_collector):
    """Test batch metric operations"""
    # Create metrics
    metrics = [
        ("test_batch_1", MetricType.COUNTER),
        ("test_batch_2", MetricType.GAUGE)
    ]
    
    await metrics_collector.create_metrics_batch(metrics)
    
    # Record batch of values
    values = [
        ("test_batch_1", 1),
        ("test_batch_2", 42.5)
    ]
    
    await metrics_collector.record_batch(values)
    
    # Verify values
    for name, _ in metrics:
        value = await metrics_collector.get_metric_value(name)
        assert value is not None

@pytest.mark.asyncio
async def test_metric_callbacks(metrics_collector):
    """Test metric update callbacks"""
    callback_values = []
    
    def update_callback(metric_name, value, labels):
        callback_values.append((metric_name, value, labels))
    
    metrics_collector.add_update_callback(update_callback)
    
    # Record metric that should trigger callback
    await metrics_collector.create_counter("test_callback", "Test callback metric")
    await metrics_collector.increment("test_callback", value=1)
    
    assert len(callback_values) == 1
    assert callback_values[0][0] == "test_callback"
    assert callback_values[0][1] == 1 