import pytest
import asyncio
from datetime import datetime, timedelta
from src.ingestion.monitoring import (
    MetricType,
    MetricValue,
    MetricCollector,
    HandlerMetrics,
    MetricsExporter
)

# Fixtures
@pytest.fixture
async def metric_collector():
    collector = MetricCollector()
    await collector.start()
    yield collector
    await collector.stop()

@pytest.fixture
def handler_metrics(metric_collector):
    return HandlerMetrics(metric_collector)

@pytest.fixture
def metrics_exporter(metric_collector):
    return MetricsExporter(metric_collector)

# Metric Collector Tests
@pytest.mark.asyncio
async def test_record_metric(metric_collector):
    await metric_collector.record_metric(
        "test_metric",
        1.0,
        MetricType.COUNTER,
        {"label": "test"}
    )
    
    metrics = await metric_collector.get_metrics("test_metric")
    assert "test_metric" in metrics
    assert MetricType.COUNTER.value in metrics["test_metric"]
    assert len(metrics["test_metric"][MetricType.COUNTER.value]) == 1
    assert metrics["test_metric"][MetricType.COUNTER.value][0].value == 1.0

@pytest.mark.asyncio
async def test_metric_filtering(metric_collector):
    # Record metrics with different timestamps
    now = datetime.utcnow()
    past = now - timedelta(hours=2)
    future = now + timedelta(hours=2)
    
    await metric_collector.record_metric("test", 1.0, MetricType.COUNTER)
    
    metrics = await metric_collector.get_metrics(
        start_time=past,
        end_time=future
    )
    assert "test" in metrics
    
    metrics = await metric_collector.get_metrics(
        start_time=future,
        end_time=None
    )
    assert "test" not in metrics

@pytest.mark.asyncio
async def test_cleanup_old_metrics(metric_collector):
    # Record a metric
    await metric_collector.record_metric("test", 1.0, MetricType.COUNTER)
    
    # Manually trigger cleanup with very short retention
    metric_collector._retention_period = timedelta(microseconds=1)
    await asyncio.sleep(0.1)
    await metric_collector._cleanup_old_metrics()
    
    metrics = await metric_collector.get_metrics("test")
    assert "test" not in metrics

# Handler Metrics Tests
@pytest.mark.asyncio
async def test_record_processing_time(handler_metrics):
    await handler_metrics.record_processing_time("test_handler", 0.5)
    
    metrics = await handler_metrics.collector.get_metrics("test_handler_processing_time")
    assert "test_handler_processing_time" in metrics
    assert MetricType.HISTOGRAM.value in metrics["test_handler_processing_time"]

@pytest.mark.asyncio
async def test_record_error(handler_metrics):
    await handler_metrics.record_error("test_handler", "ValueError")
    
    metrics = await handler_metrics.collector.get_metrics("test_handler_errors")
    assert "test_handler_errors" in metrics
    assert MetricType.COUNTER.value in metrics["test_handler_errors"]

@pytest.mark.asyncio
async def test_record_success(handler_metrics):
    await handler_metrics.record_success("test_handler")
    
    metrics = await handler_metrics.collector.get_metrics("test_handler_success")
    assert "test_handler_success" in metrics
    assert MetricType.COUNTER.value in metrics["test_handler_success"]

# Metrics Exporter Tests
@pytest.mark.asyncio
async def test_export_json(metrics_exporter, handler_metrics):
    # Record some test metrics
    await handler_metrics.record_success("test_handler")
    await handler_metrics.record_error("test_handler", "TestError")
    
    json_output = await metrics_exporter.export_json()
    assert isinstance(json_output, str)
    assert "test_handler_success" in json_output
    assert "test_handler_errors" in json_output

@pytest.mark.asyncio
async def test_export_prometheus(metrics_exporter, handler_metrics):
    # Record some test metrics
    await handler_metrics.record_success("test_handler")
    await handler_metrics.record_processing_time("test_handler", 0.5)
    
    prom_output = await metrics_exporter.export_prometheus()
    assert isinstance(prom_output, str)
    assert "# TYPE test_handler_success counter" in prom_output
    assert "# TYPE test_handler_processing_time histogram" in prom_output

# Integration Tests
@pytest.mark.asyncio
async def test_metrics_integration(handler_metrics):
    # Simulate a complete processing cycle
    await handler_metrics.record_processing_time("test_handler", 0.5)
    await handler_metrics.record_data_size("test_handler", 1000)
    await handler_metrics.record_success("test_handler")
    
    metrics = await handler_metrics.collector.get_metrics()
    
    # Verify all metrics were recorded
    assert "test_handler_processing_time" in metrics
    assert "test_handler_data_size" in metrics
    assert "test_handler_success" in metrics
    
    # Verify metric types
    assert MetricType.HISTOGRAM.value in metrics["test_handler_processing_time"]
    assert MetricType.HISTOGRAM.value in metrics["test_handler_data_size"]
    assert MetricType.COUNTER.value in metrics["test_handler_success"]

@pytest.mark.asyncio
async def test_error_handling_flow(handler_metrics):
    # Simulate processing with errors
    await handler_metrics.record_processing_time("test_handler", 0.1)
    await handler_metrics.record_error("test_handler", "ValueError")
    
    metrics = await handler_metrics.collector.get_metrics()
    
    # Verify error was recorded
    assert "test_handler_errors" in metrics
    error_metrics = metrics["test_handler_errors"][MetricType.COUNTER.value]
    assert any(
        m.labels.get("error") == "ValueError"
        for m in error_metrics
    )

@pytest.mark.asyncio
async def test_concurrent_metric_recording(handler_metrics):
    # Test concurrent metric recording
    async def record_metrics():
        for _ in range(10):
            await handler_metrics.record_success("test_handler")
            await asyncio.sleep(0.01)
    
    # Run multiple concurrent recording tasks
    tasks = [record_metrics() for _ in range(5)]
    await asyncio.gather(*tasks)
    
    metrics = await handler_metrics.collector.get_metrics("test_handler_success")
    success_count = len(metrics["test_handler_success"][MetricType.COUNTER.value])
    assert success_count == 50  # 5 tasks * 10 records each 