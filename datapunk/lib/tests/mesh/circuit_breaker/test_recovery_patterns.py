"""Tests for circuit breaker recovery patterns"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from datapunk_shared.mesh.circuit_breaker.recovery_patterns import (
    FallbackChain,
    FallbackResult,
    ExponentialBackoffPattern,
    PartialRecoveryPattern,
    AdaptiveRecoveryPattern
)

@pytest.fixture
def mock_cache():
    cache = AsyncMock()
    cache.get = AsyncMock()
    cache.set = AsyncMock()
    return cache

@pytest.fixture
def mock_metrics():
    metrics = AsyncMock()
    metrics.increment = AsyncMock()
    metrics.gauge = AsyncMock()
    metrics.get_gauge = AsyncMock()
    return metrics

class TestFallbackChain:
    async def test_primary_success(self, mock_cache, mock_metrics):
        chain = FallbackChain(mock_cache, mock_metrics)
        primary = AsyncMock(return_value="success")
        
        result = await chain.execute(primary, cache_key="test")
        
        assert result.value == "success"
        assert not result.fallback_used
        assert not result.degraded
        mock_cache.set.assert_awaited_once()
        
    async def test_cache_fallback(self, mock_cache, mock_metrics):
        chain = FallbackChain(mock_cache, mock_metrics)
        primary = AsyncMock(side_effect=Exception("primary failed"))
        mock_cache.get.return_value = "cached"
        
        result = await chain.execute(primary, cache_key="test")
        
        assert result.value == "cached"
        assert result.fallback_used
        assert result.degraded
        mock_metrics.increment.assert_awaited_once_with(
            "circuit_breaker_cache_fallback_used"
        )
        
    async def test_handler_fallback(self, mock_cache, mock_metrics):
        chain = FallbackChain(mock_cache, mock_metrics)
        primary = AsyncMock(side_effect=Exception("primary failed"))
        mock_cache.get.return_value = None
        fallback = AsyncMock(return_value="fallback")
        chain.add_fallback(fallback)
        
        result = await chain.execute(primary)
        
        assert result.value == "fallback"
        assert result.fallback_used
        assert result.degraded
        mock_metrics.increment.assert_awaited_once_with(
            "circuit_breaker_fallback_used"
        )
        
    async def test_all_failures(self, mock_cache, mock_metrics):
        chain = FallbackChain(mock_cache, mock_metrics)
        primary = AsyncMock(side_effect=Exception("primary failed"))
        fallback = AsyncMock(side_effect=Exception("fallback failed"))
        chain.add_fallback(fallback)
        
        result = await chain.execute(primary)
        
        assert result.error is not None
        assert isinstance(result.error, Exception)
        assert str(result.error) == "primary failed"

class TestExponentialBackoffPattern:
    async def test_initial_recovery_attempt(self):
        pattern = ExponentialBackoffPattern()
        last_failure = datetime.utcnow() - timedelta(seconds=2)
        
        should_attempt = await pattern.should_attempt_recovery(1, last_failure)
        
        assert should_attempt
        
    async def test_exponential_delay(self):
        pattern = ExponentialBackoffPattern(base_delay=1.0)
        pattern.attempt = 2
        last_failure = datetime.utcnow() - timedelta(seconds=3)
        
        should_attempt = await pattern.should_attempt_recovery(1, last_failure)
        
        assert not should_attempt  # 2^2 = 4 seconds needed
        
    async def test_max_retries(self):
        pattern = ExponentialBackoffPattern(max_retries=3)
        pattern.attempt = 3
        last_failure = datetime.utcnow() - timedelta(seconds=100)
        
        should_attempt = await pattern.should_attempt_recovery(1, last_failure)
        
        assert not should_attempt
        
    async def test_success_reset(self):
        pattern = ExponentialBackoffPattern()
        pattern.attempt = 2
        
        reset = await pattern.handle_success(3)
        
        assert reset
        assert pattern.attempt == 0

class TestPartialRecoveryPattern:
    @pytest.fixture
    def pattern(self, mock_metrics):
        return PartialRecoveryPattern(
            feature_priorities={
                "critical": 3,
                "important": 2,
                "optional": 1
            },
            metrics=mock_metrics
        )
        
    async def test_initial_recovery(self, pattern):
        should_attempt = await pattern.should_attempt_recovery(
            1,
            datetime.utcnow()
        )
        assert should_attempt
        
    async def test_feature_enablement(self, pattern, mock_metrics):
        await pattern.handle_success(5)
        
        assert "critical" in pattern.enabled_features
        mock_metrics.increment.assert_awaited_once()
        
    async def test_feature_disablement(self, pattern, mock_metrics):
        pattern.enabled_features = {"critical", "optional"}
        
        await pattern.handle_failure(1)
        
        assert "optional" not in pattern.enabled_features
        assert "critical" in pattern.enabled_features
        mock_metrics.increment.assert_awaited_once()
        
    async def test_complete_recovery(self, pattern):
        pattern.enabled_features = {
            "critical",
            "important",
            "optional"
        }
        
        complete = await pattern.handle_success(5)
        assert complete

class TestAdaptiveRecoveryPattern:
    @pytest.fixture
    def pattern(self, mock_metrics):
        return AdaptiveRecoveryPattern(mock_metrics)
        
    async def test_healthy_metrics(self, pattern, mock_metrics):
        mock_metrics.get_gauge.side_effect = [50.0, 60.0, 70.0]
        
        should_attempt = await pattern.should_attempt_recovery(
            1,
            datetime.utcnow()
        )
        
        assert should_attempt
        
    async def test_unhealthy_metrics(self, pattern, mock_metrics):
        mock_metrics.get_gauge.side_effect = [150.0, 90.0, 70.0]
        
        should_attempt = await pattern.should_attempt_recovery(
            1,
            datetime.utcnow()
        )
        
        assert not should_attempt
        
    async def test_rate_increase(self, pattern, mock_metrics):
        pattern.current_rate = 0.5
        
        await pattern.handle_success(10)
        
        assert pattern.current_rate == 0.6
        mock_metrics.gauge.assert_awaited_once()
        
    async def test_rate_decrease(self, pattern, mock_metrics):
        pattern.current_rate = 0.5
        
        await pattern.handle_failure(1)
        
        assert pattern.current_rate == 0.3
        mock_metrics.gauge.assert_awaited_once()
        
    async def test_metric_error_handling(self, pattern, mock_metrics):
        mock_metrics.get_gauge.side_effect = Exception("metric error")
        
        should_attempt = await pattern.should_attempt_recovery(
            1,
            datetime.utcnow()
        )
        
        assert not should_attempt 