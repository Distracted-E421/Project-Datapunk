"""Tests for adaptive timeout management"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import numpy as np
from datapunk_shared.mesh.circuit_breaker.adaptive_timeout import (
    TimeoutStrategy,
    TimeoutConfig,
    ResponseTimeTracker,
    AdaptiveTimeout
)

@pytest.fixture
def mock_metrics():
    metrics = AsyncMock()
    metrics.gauge = AsyncMock()
    return metrics

@pytest.fixture
def timeout_config():
    return TimeoutConfig(
        min_timeout_ms=100.0,
        max_timeout_ms=5000.0,
        initial_timeout_ms=1000.0,
        strategy=TimeoutStrategy.HYBRID,
        window_size=10,
        percentile=95.0,
        adjustment_factor=1.5
    )

@pytest.fixture
def response_tracker():
    return ResponseTimeTracker(window_size=10)

@pytest.fixture
def adaptive_timeout(mock_metrics, timeout_config):
    return AdaptiveTimeout(
        config=timeout_config,
        metrics_client=mock_metrics
    )

class TestTimeoutConfig:
    def test_default_config(self):
        config = TimeoutConfig()
        
        assert config.min_timeout_ms == 100.0
        assert config.max_timeout_ms == 30000.0
        assert config.initial_timeout_ms == 1000.0
        assert config.strategy == TimeoutStrategy.HYBRID
        assert config.window_size == 100
        assert config.percentile == 95.0
        assert config.adjustment_factor == 1.5
        
    def test_custom_config(self):
        config = TimeoutConfig(
            min_timeout_ms=200.0,
            max_timeout_ms=10000.0,
            initial_timeout_ms=500.0,
            strategy=TimeoutStrategy.ADAPTIVE,
            window_size=50,
            percentile=90.0,
            adjustment_factor=2.0
        )
        
        assert config.min_timeout_ms == 200.0
        assert config.max_timeout_ms == 10000.0
        assert config.initial_timeout_ms == 500.0
        assert config.strategy == TimeoutStrategy.ADAPTIVE
        assert config.window_size == 50
        assert config.percentile == 90.0
        assert config.adjustment_factor == 2.0

class TestResponseTimeTracker:
    def test_add_response_time(self, response_tracker):
        response_tracker.add_response_time(100.0, True)
        
        assert len(response_tracker.response_times) == 1
        assert len(response_tracker.success_times) == 1
        assert len(response_tracker.failure_times) == 0
        
    def test_window_size_limit(self, response_tracker):
        window_size = response_tracker.window_size
        
        # Add more than window size
        for i in range(window_size + 5):
            response_tracker.add_response_time(float(i))
            
        assert len(response_tracker.response_times) == window_size
        assert float(window_size + 4) in response_tracker.response_times
        
    def test_get_percentile(self, response_tracker):
        values = [100.0, 200.0, 300.0, 400.0, 500.0]
        for v in values:
            response_tracker.add_response_time(v)
            
        p95 = response_tracker.get_percentile(95.0)
        assert p95 >= max(values) * 0.9  # Close to max
        
    def test_get_success_rate(self, response_tracker):
        # Add mix of successes and failures
        response_tracker.add_response_time(100.0, True)
        response_tracker.add_response_time(200.0, True)
        response_tracker.add_response_time(300.0, False)
        
        assert response_tracker.get_success_rate() == 2/3
        
    def test_get_stats_empty(self, response_tracker):
        stats = response_tracker.get_stats()
        
        assert stats["mean"] == 0.0
        assert stats["std"] == 0.0
        assert stats["min"] == 0.0
        assert stats["max"] == 0.0
        assert stats["success_rate"] == 1.0
        
    def test_get_stats_with_data(self, response_tracker):
        values = [100.0, 200.0, 300.0]
        for v in values:
            response_tracker.add_response_time(v)
            
        stats = response_tracker.get_stats()
        
        assert stats["mean"] == 200.0
        assert stats["min"] == 100.0
        assert stats["max"] == 300.0
        assert stats["success_rate"] == 1.0

class TestAdaptiveTimeout:
    async def test_record_response_time(self, adaptive_timeout):
        await adaptive_timeout.record_response_time(100.0)
        
        assert len(adaptive_timeout.tracker.response_times) == 1
        adaptive_timeout.metrics.gauge.assert_called_once()
        
    async def test_get_timeout_percentile(self, adaptive_timeout):
        adaptive_timeout.config.strategy = TimeoutStrategy.PERCENTILE
        
        # Add some response times
        for i in range(5):
            await adaptive_timeout.record_response_time(100.0 * (i + 1))
            
        timeout = await adaptive_timeout.get_timeout()
        assert timeout > adaptive_timeout.config.min_timeout_ms
        assert timeout < adaptive_timeout.config.max_timeout_ms
        
    async def test_get_timeout_adaptive(self, adaptive_timeout):
        adaptive_timeout.config.strategy = TimeoutStrategy.ADAPTIVE
        
        # Add some response times with failures
        for i in range(5):
            await adaptive_timeout.record_response_time(
                100.0 * (i + 1),
                is_success=(i % 2 == 0)
            )
            
        timeout = await adaptive_timeout.get_timeout()
        assert timeout > adaptive_timeout.config.min_timeout_ms
        assert timeout < adaptive_timeout.config.max_timeout_ms
        
    async def test_get_timeout_hybrid(self, adaptive_timeout):
        # Add some response times
        for i in range(5):
            await adaptive_timeout.record_response_time(100.0 * (i + 1))
            
        timeout = await adaptive_timeout.get_timeout()
        assert timeout > adaptive_timeout.config.min_timeout_ms
        assert timeout < adaptive_timeout.config.max_timeout_ms
        
    async def test_timeout_bounds(self, adaptive_timeout):
        # Test minimum bound
        await adaptive_timeout.record_response_time(1.0)  # Very fast
        timeout = await adaptive_timeout.get_timeout()
        assert timeout >= adaptive_timeout.config.min_timeout_ms
        
        # Test maximum bound
        await adaptive_timeout.record_response_time(100000.0)  # Very slow
        timeout = await adaptive_timeout.get_timeout()
        assert timeout <= adaptive_timeout.config.max_timeout_ms
        
    async def test_adjustment_history(self, adaptive_timeout):
        # Record times that will cause adjustment
        await adaptive_timeout.record_response_time(100.0)
        first_timeout = await adaptive_timeout.get_timeout()
        
        await adaptive_timeout.record_response_time(1000.0)
        second_timeout = await adaptive_timeout.get_timeout()
        
        assert len(adaptive_timeout.adjustment_history) > 0
        assert first_timeout != second_timeout
        
    def test_get_timeout_metrics(self, adaptive_timeout):
        # Add some response times
        for i in range(5):
            adaptive_timeout.tracker.add_response_time(100.0 * (i + 1))
            
        metrics = adaptive_timeout.get_timeout_metrics()
        
        assert "current_timeout" in metrics
        assert "success_rate" in metrics
        assert "mean_response_time" in metrics
        assert "max_response_time" in metrics
        assert "std_response_time" in metrics 