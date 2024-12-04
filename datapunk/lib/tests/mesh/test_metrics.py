import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.metrics import (
    MetricsCollector,
    MetricsAggregator,
    MetricsConfig,
    MetricType,
    MetricsError
)

@pytest.fixture
def metrics_config():
    return MetricsConfig(
        collection_interval=1,
        retention_days=7,
        batch_size=100
    )

@pytest.fixture
def metrics_collector(metrics_config):
    return MetricsCollector(config=metrics_config)

@pytest.fixture
def metrics_aggregator():
    return MetricsAggregator()

@pytest.mark.asyncio
async def test_metrics_collection(metrics_collector):
    # Record some test metrics
    metrics_collector.record_counter("requests_total", 1)
    metrics_collector.record_gauge("active_connections", 5)
    metrics_collector.record_histogram("response_time", 0.1)
    
    metrics = await metrics_collector.collect()
    
    assert "requests_total" in metrics
    assert "active_connections" in metrics
    assert "response_time" in metrics

@pytest.mark.asyncio
async def test_metrics_aggregation(metrics_aggregator):
    metrics_data = [
        {"name": "requests", "type": MetricType.COUNTER, "value": 1},
        {"name": "requests", "type": MetricType.COUNTER, "value": 2},
        {"name": "requests", "type": MetricType.COUNTER, "value": 3}
    ]
    
    result = await metrics_aggregator.aggregate(metrics_data)
    assert result["requests"] == 6

@pytest.mark.asyncio
async def test_metrics_persistence(metrics_collector):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        await metrics_collector.persist_metrics([
            {"name": "test", "value": 1, "timestamp": datetime.utcnow()}
        ])
        
        mock_file.write.assert_called_once()

@pytest.mark.asyncio
async def test_metrics_cleanup(metrics_collector):
    with patch('pathlib.Path.glob') as mock_glob:
        mock_glob.return_value = [
            Mock(stat=lambda: Mock(st_mtime=datetime.now().timestamp() - 8*24*3600))
        ]
        
        await metrics_collector.cleanup_old_metrics()
        assert mock_glob.called

@pytest.mark.asyncio
async def test_histogram_metrics(metrics_collector):
    # Record response times
    times = [0.1, 0.2, 0.3, 0.4, 0.5]
    for t in times:
        metrics_collector.record_histogram("response_time", t)
    
    metrics = await metrics_collector.collect()
    histogram = metrics["response_time"]
    
    assert histogram["avg"] == pytest.approx(0.3)
    assert histogram["p95"] >= 0.4
    assert histogram["p99"] >= 0.5

@pytest.mark.asyncio
async def test_rate_metrics(metrics_collector):
    # Record requests over time
    for _ in range(10):
        metrics_collector.record_counter("requests_per_second", 1)
        await asyncio.sleep(0.1)
    
    metrics = await metrics_collector.collect()
    assert metrics["requests_per_second"] >= 9  # Allow for timing variations

@pytest.mark.asyncio
async def test_metrics_tags(metrics_collector):
    metrics_collector.record_counter(
        "requests_total",
        1,
        tags={"service": "api", "endpoint": "/users"}
    )
    
    metrics = await metrics_collector.collect()
    assert "service" in metrics["requests_total"]["tags"]
    assert "endpoint" in metrics["requests_total"]["tags"]

@pytest.mark.asyncio
async def test_metrics_batch_processing(metrics_collector):
    # Generate more metrics than batch size
    for i in range(150):  # Config batch_size is 100
        metrics_collector.record_counter("test_metric", i)
    
    with patch.object(metrics_collector, '_send_batch') as mock_send:
        await metrics_collector.flush()
        assert mock_send.call_count == 2  # Should be called twice for 150 items

@pytest.mark.asyncio
async def test_metrics_error_handling(metrics_collector):
    with patch.object(metrics_collector, '_send_batch', side_effect=Exception("Network error")):
        with pytest.raises(MetricsError):
            await metrics_collector.flush()

@pytest.mark.asyncio
async def test_metrics_aggregation_window(metrics_aggregator):
    now = datetime.utcnow()
    metrics_data = [
        {
            "name": "requests",
            "type": MetricType.COUNTER,
            "value": 1,
            "timestamp": now - timedelta(minutes=1)
        },
        {
            "name": "requests",
            "type": MetricType.COUNTER,
            "value": 2,
            "timestamp": now
        }
    ]
    
    # Aggregate last 30 seconds
    result = await metrics_aggregator.aggregate(
        metrics_data,
        window_seconds=30
    )
    assert result["requests"] == 2  # Only the recent metric

@pytest.mark.asyncio
async def test_metrics_collection_interval(metrics_collector):
    with patch.object(metrics_collector, 'collect') as mock_collect:
        await metrics_collector.start_collection()
        await asyncio.sleep(1.1)  # Slightly more than collection_interval
        await metrics_collector.stop_collection()
        
        assert mock_collect.call_count >= 1

@pytest.mark.asyncio
async def test_custom_metric_types(metrics_collector):
    # Test custom metric type registration and collection
    metrics_collector.register_custom_type(
        "success_ratio",
        lambda values: sum(v["success"] for v in values) / len(values)
    )
    
    metrics_collector.record_custom(
        "api_success",
        "success_ratio",
        {"success": True}
    )
    
    metrics = await metrics_collector.collect()
    assert "api_success" in metrics