"""Tests for the Circuit Breaker Metrics Collector"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import numpy as np
from datapunk_shared.mesh.circuit_breaker.metrics_collector import (
    CircuitBreakerMetricsCollector,
    CircuitMetricsConfig,
    MetricsBucket
)

@pytest.fixture
def metrics_config():
    return CircuitMetricsConfig(
        window_size=5,
        bucket_size=1,
        percentiles=[50, 90, 95, 99],
        anomaly_threshold=2.0,
        trend_window=10
    )

@pytest.fixture
def collector(metrics_config):
    return CircuitBreakerMetricsCollector(metrics_config)

@pytest.mark.asyncio
async def test_record_request(collector):
    """Test basic request recording"""
    await collector.record_request(100.0, False)
    await collector.record_request(200.0, True)
    
    metrics = await collector.get_metrics()
    assert metrics["total_requests"] == 2
    assert metrics["total_errors"] == 1
    assert metrics["error_rate"] == 0.5

@pytest.mark.asyncio
async def test_latency_percentiles(collector):
    """Test latency percentile calculations"""
    latencies = [100.0, 200.0, 300.0, 400.0, 500.0]
    for latency in latencies:
        await collector.record_request(latency, False)
    
    metrics = await collector.get_metrics()
    percentiles = metrics["latency_percentiles"]
    
    assert percentiles["p50"] == pytest.approx(300.0)
    assert percentiles["p90"] == pytest.approx(460.0)
    assert percentiles["p95"] == pytest.approx(480.0)
    assert percentiles["p99"] == pytest.approx(496.0)

@pytest.mark.asyncio
async def test_circuit_trip_patterns(collector):
    """Test circuit trip pattern detection"""
    # Simulate regular trip pattern
    for _ in range(5):
        await collector.record_circuit_trip()
        await asyncio.sleep(1)
    
    metrics = await collector.get_metrics()
    assert metrics["circuit_trips"] == 5
    assert len(metrics["known_patterns"]) > 0

@pytest.mark.asyncio
async def test_anomaly_detection(collector):
    """Test anomaly detection in metrics"""
    # Establish baseline
    for _ in range(10):
        await collector.record_request(100.0, False)
    
    # Introduce anomaly
    with patch.object(collector.logger, 'warning') as mock_warning:
        await collector.record_request(500.0, False)
        mock_warning.assert_called_once()

@pytest.mark.asyncio
async def test_resource_tracking(collector):
    """Test resource usage tracking"""
    await collector.record_resource_usage("cpu", 50.0)
    await collector.record_resource_usage("memory", 75.0)
    
    metrics = await collector.get_metrics()
    assert "cpu" in metrics["resource_usage"]
    assert "memory" in metrics["resource_usage"]
    assert metrics["resource_usage"]["cpu"]["current"] == 50.0
    assert metrics["resource_usage"]["memory"]["current"] == 75.0

@pytest.mark.asyncio
async def test_health_status(collector):
    """Test health status calculation"""
    # Simulate healthy state
    for _ in range(10):
        await collector.record_request(100.0, False)
    
    health = await collector.get_health_status()
    assert health["status"] == "healthy"
    assert health["overall_health"] > 0.8
    
    # Simulate degraded state
    for _ in range(5):
        await collector.record_request(2000.0, True)
    
    health = await collector.get_health_status()
    assert health["status"] == "degraded"
    assert 0.5 <= health["overall_health"] <= 0.8

@pytest.mark.asyncio
async def test_trend_analysis(collector):
    """Test trend analysis functionality"""
    # Simulate increasing error rate
    for i in range(5):
        errors = i
        successes = 10 - i
        for _ in range(errors):
            await collector.record_request(100.0, True)
        for _ in range(successes):
            await collector.record_request(100.0, False)
        await asyncio.sleep(1)
    
    metrics = await collector.get_metrics()
    assert "error_rates_trend" in metrics["trends"]
    assert metrics["trends"]["error_rates_trend"] > 0  # Increasing trend

@pytest.mark.asyncio
async def test_cleanup_old_metrics(collector):
    """Test cleanup of old metrics"""
    # Fill buckets
    for _ in range(10):
        await collector.record_request(100.0, False)
        await asyncio.sleep(1)
    
    # Wait for cleanup
    await asyncio.sleep(collector.config.window_size + 1)
    
    metrics = await collector.get_metrics()
    assert metrics["total_requests"] <= collector.config.window_size

@pytest.mark.asyncio
async def test_recovery_tracking(collector):
    """Test recovery attempt tracking"""
    await collector.record_recovery_attempt(True)
    await collector.record_recovery_attempt(False)
    await collector.record_recovery_attempt(True)
    
    bucket = collector.current_bucket
    assert bucket.recovery_attempts == 3
    assert bucket.partial_success == 2

@pytest.mark.asyncio
async def test_concurrent_updates(collector):
    """Test concurrent metric updates"""
    async def update_metrics():
        for _ in range(100):
            await collector.record_request(100.0, False)
            await asyncio.sleep(0.01)
    
    # Run multiple concurrent updates
    tasks = [update_metrics() for _ in range(5)]
    await asyncio.gather(*tasks)
    
    metrics = await collector.get_metrics()
    assert metrics["total_requests"] == 500

@pytest.mark.asyncio
async def test_metrics_persistence(collector):
    """Test metrics persistence across buckets"""
    # Record metrics across multiple buckets
    for i in range(3):
        await collector.record_request(100.0 * (i + 1), False)
        await asyncio.sleep(collector.config.bucket_size)
    
    metrics = await collector.get_metrics()
    assert metrics["total_requests"] == 3
    assert len(collector.buckets) > 1

@pytest.mark.asyncio
async def test_error_handling(collector):
    """Test error handling in metrics collection"""
    with patch.object(collector.logger, 'error') as mock_error:
        # Force an error in cleanup loop
        with patch.object(collector, '_update_trends', 
                         side_effect=Exception("Test error")):
            await collector._cleanup_loop()
            mock_error.assert_called_once()

@pytest.mark.asyncio
async def test_resource_baseline_calculation(collector):
    """Test resource baseline calculation"""
    # Record series of resource usage
    usages = [50.0, 60.0, 70.0, 80.0, 90.0]
    for usage in usages:
        await collector.record_resource_usage("cpu", usage)
    
    metrics = await collector.get_metrics()
    baseline = metrics["resource_usage"]["cpu"]["baseline"]
    assert 50.0 < baseline < 90.0  # Should be somewhere in between

@pytest.mark.asyncio
async def test_pattern_detection_sensitivity(collector):
    """Test pattern detection sensitivity"""
    # Simulate regular pattern
    for _ in range(5):
        await collector.record_circuit_trip()
        await asyncio.sleep(1)
    
    # Simulate irregular pattern
    for _ in range(5):
        await collector.record_circuit_trip()
        await asyncio.sleep(np.random.uniform(0.5, 1.5))
    
    metrics = await collector.get_metrics()
    # Should detect only the regular pattern
    assert len(metrics["known_patterns"]) == 1 