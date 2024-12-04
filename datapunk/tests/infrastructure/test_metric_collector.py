import pytest
import asyncio
import json
from datetime import datetime, timedelta
from datapunk.lib.monitoring.metric_collector import (
    MetricType, AggregationType, MetricValue, MetricDefinition,
    MetricAggregator, MetricStorage, MetricCollector
)

@pytest.fixture
def metric_definition():
    return MetricDefinition(
        name="test_metric",
        type=MetricType.GAUGE,
        description="Test metric",
        unit="count",
        aggregations=[
            AggregationType.SUM,
            AggregationType.AVG,
            AggregationType.MIN,
            AggregationType.MAX
        ],
        retention_period=timedelta(hours=1)
    )

@pytest.fixture
def labeled_metric_definition():
    return MetricDefinition(
        name="labeled_metric",
        type=MetricType.COUNTER,
        description="Test labeled metric",
        unit="bytes",
        aggregations=[AggregationType.SUM],
        retention_period=timedelta(hours=1),
        labels=["service", "endpoint"]
    )

@pytest.fixture
def metric_collector():
    return MetricCollector()

@pytest.mark.asyncio
async def test_metric_registration(metric_collector, metric_definition):
    metric_collector.register_metric(metric_definition)
    assert "test_metric" in metric_collector.definitions
    assert len(metric_collector.aggregators["test_metric"]) == 5  # 5 time windows
    
    # Test duplicate registration
    with pytest.raises(ValueError, match="already registered"):
        metric_collector.register_metric(metric_definition)

@pytest.mark.asyncio
async def test_metric_recording(metric_collector, metric_definition):
    metric_collector.register_metric(metric_definition)
    
    # Record some values
    metric_collector.record_metric("test_metric", 10)
    metric_collector.record_metric("test_metric", 20)
    metric_collector.record_metric("test_metric", 30)
    
    # Test aggregations
    value = metric_collector.get_metric_aggregation(
        "test_metric", "1min", AggregationType.SUM
    )
    assert value == 60
    
    value = metric_collector.get_metric_aggregation(
        "test_metric", "1min", AggregationType.AVG
    )
    assert value == 20
    
    value = metric_collector.get_metric_aggregation(
        "test_metric", "1min", AggregationType.MIN
    )
    assert value == 10
    
    value = metric_collector.get_metric_aggregation(
        "test_metric", "1min", AggregationType.MAX
    )
    assert value == 30

@pytest.mark.asyncio
async def test_labeled_metrics(metric_collector, labeled_metric_definition):
    metric_collector.register_metric(labeled_metric_definition)
    
    # Record values with labels
    metric_collector.record_metric(
        "labeled_metric",
        100,
        labels={"service": "api", "endpoint": "/users"}
    )
    
    metric_collector.record_metric(
        "labeled_metric",
        200,
        labels={"service": "api", "endpoint": "/orders"}
    )
    
    # Test filtering by labels
    values = metric_collector.get_metric_values(
        "labeled_metric",
        labels={"service": "api", "endpoint": "/users"}
    )
    assert len(values) == 1
    assert values[0].value == 100
    
    # Test missing required labels
    with pytest.raises(ValueError, match="Labels required"):
        metric_collector.record_metric("labeled_metric", 300)
    
    with pytest.raises(ValueError, match="Missing required labels"):
        metric_collector.record_metric(
            "labeled_metric",
            300,
            labels={"service": "api"}  # Missing endpoint label
        )

@pytest.mark.asyncio
async def test_metric_storage_cleanup(metric_collector, metric_definition):
    # Set a short retention period for testing
    metric_definition.retention_period = timedelta(seconds=2)
    metric_collector.register_metric(metric_definition)
    
    # Record a value
    metric_collector.record_metric("test_metric", 10)
    
    # Verify value exists
    values = metric_collector.get_metric_values("test_metric")
    assert len(values) == 1
    
    # Wait for retention period to expire
    await asyncio.sleep(2.1)
    
    # Start collector to trigger cleanup
    await metric_collector.start()
    await asyncio.sleep(0.1)  # Wait for first cleanup
    
    # Verify value was cleaned up
    values = metric_collector.get_metric_values("test_metric")
    assert len(values) == 0
    
    await metric_collector.stop()

@pytest.mark.asyncio
async def test_metric_export(metric_collector, metric_definition):
    metric_collector.register_metric(metric_definition)
    
    # Record some values
    metric_collector.record_metric("test_metric", 10)
    metric_collector.record_metric("test_metric", 20)
    
    # Export metrics
    exported = metric_collector.export_metrics()
    data = json.loads(exported)
    
    assert "test_metric" in data
    assert data["test_metric"]["type"] == "gauge"
    assert data["test_metric"]["unit"] == "count"
    assert len(data["test_metric"]["values"]) == 5  # One for each time window
    
    # Test invalid format
    with pytest.raises(ValueError, match="Only JSON format"):
        metric_collector.export_metrics("xml")

@pytest.mark.asyncio
async def test_metric_aggregator():
    aggregator = MetricAggregator(timedelta(minutes=1))
    
    # Add some values
    values = [
        MetricValue(value=10, timestamp=datetime.now()),
        MetricValue(value=20, timestamp=datetime.now()),
        MetricValue(value=30, timestamp=datetime.now()),
        MetricValue(value=40, timestamp=datetime.now()),
        MetricValue(value=50, timestamp=datetime.now())
    ]
    
    for value in values:
        aggregator.add_value(value)
    
    # Test different aggregations
    assert aggregator.get_aggregation(AggregationType.SUM) == 150
    assert aggregator.get_aggregation(AggregationType.AVG) == 30
    assert aggregator.get_aggregation(AggregationType.MIN) == 10
    assert aggregator.get_aggregation(AggregationType.MAX) == 50
    assert aggregator.get_aggregation(AggregationType.COUNT) == 5
    assert aggregator.get_aggregation(AggregationType.P50) == 30
    assert aggregator.get_aggregation(AggregationType.P90) == 50
    assert aggregator.get_aggregation(AggregationType.P95) == 50
    assert aggregator.get_aggregation(AggregationType.P99) == 50
    
    # Test invalid aggregation type
    with pytest.raises(ValueError, match="Unsupported aggregation type"):
        aggregator.get_aggregation("invalid")

@pytest.mark.asyncio
async def test_metric_storage():
    storage = MetricStorage(timedelta(minutes=1))
    
    # Store some values
    now = datetime.now()
    old_time = now - timedelta(minutes=2)
    
    storage.store_metric("test", MetricValue(10, now))
    storage.store_metric("test", MetricValue(20, old_time))
    
    # Test filtering by time range
    values = storage.get_metrics(
        "test",
        start_time=now - timedelta(minutes=1),
        end_time=now + timedelta(minutes=1)
    )
    assert len(values) == 1
    assert values[0].value == 10
    
    # Test cleanup of old metrics
    storage._cleanup_old_metrics("test")
    values = storage.get_metrics("test")
    assert len(values) == 1
    assert values[0].value == 10

@pytest.mark.asyncio
async def test_collector_lifecycle(metric_collector, metric_definition):
    metric_collector.register_metric(metric_definition)
    
    # Start collector
    await metric_collector.start()
    assert metric_collector._running
    assert metric_collector._aggregation_task is not None
    
    # Stop collector
    await metric_collector.stop()
    assert not metric_collector._running
    assert metric_collector._aggregation_task is None
    
    # Test double start/stop
    await metric_collector.start()
    await metric_collector.start()  # Should not create multiple tasks
    assert len([task for task in asyncio.all_tasks() 
               if task._coro.__name__ == "_run_aggregation"]) == 1
    
    await metric_collector.stop()
    await metric_collector.stop()  # Should not error 