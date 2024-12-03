"""Tests for advanced circuit breaker implementation"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from datapunk_shared.mesh.circuit_breaker.circuit_breaker_advanced import (
    AdvancedCircuitBreaker,
    CircuitState
)
from datapunk_shared.mesh.circuit_breaker.recovery_patterns import (
    RecoveryPattern,
    ExponentialBackoffPattern,
    PartialRecoveryPattern,
    AdaptiveRecoveryPattern
)
from datapunk_shared.exceptions import CircuitBreakerError

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

@pytest.fixture
def mock_recovery_pattern():
    pattern = AsyncMock(spec=RecoveryPattern)
    pattern.should_attempt_recovery = AsyncMock()
    pattern.handle_success = AsyncMock()
    pattern.handle_failure = AsyncMock()
    return pattern

@pytest.fixture
def circuit_breaker(mock_cache, mock_metrics, mock_recovery_pattern):
    return AdvancedCircuitBreaker(
        service_name="test_service",
        metrics=mock_metrics,
        cache=mock_cache,
        recovery_pattern=mock_recovery_pattern
    )

class TestAdvancedCircuitBreaker:
    async def test_initial_state(self, circuit_breaker, mock_cache):
        mock_cache.get.return_value = None
        
        state = await circuit_breaker._get_cached_state()
        
        assert state == CircuitState.CLOSED
        
    async def test_allow_request_closed(self, circuit_breaker, mock_cache):
        mock_cache.get.return_value = CircuitState.CLOSED.value
        
        allowed = await circuit_breaker.allow_request()
        
        assert allowed
        
    async def test_allow_request_open_with_recovery(self,
                                                  circuit_breaker,
                                                  mock_cache,
                                                  mock_recovery_pattern):
        mock_cache.get.return_value = CircuitState.OPEN.value
        mock_recovery_pattern.should_attempt_recovery.return_value = True
        
        allowed = await circuit_breaker.allow_request()
        
        assert allowed
        mock_recovery_pattern.should_attempt_recovery.assert_awaited_once()
        
    async def test_allow_request_open_no_recovery(self,
                                                circuit_breaker,
                                                mock_cache,
                                                mock_recovery_pattern,
                                                mock_metrics):
        mock_cache.get.return_value = CircuitState.OPEN.value
        mock_recovery_pattern.should_attempt_recovery.return_value = False
        
        allowed = await circuit_breaker.allow_request()
        
        assert not allowed
        mock_metrics.increment.assert_awaited_once_with(
            "circuit_breaker_rejections",
            {"service": "test_service"}
        )
        
    async def test_record_success_half_open(self,
                                          circuit_breaker,
                                          mock_recovery_pattern):
        circuit_breaker.state = CircuitState.HALF_OPEN
        mock_recovery_pattern.handle_success.return_value = True
        
        await circuit_breaker.record_success()
        
        mock_recovery_pattern.handle_success.assert_awaited_once()
        assert circuit_breaker.state == CircuitState.CLOSED
        
    async def test_record_failure(self,
                                circuit_breaker,
                                mock_recovery_pattern,
                                mock_metrics):
        await circuit_breaker.record_failure()
        
        mock_recovery_pattern.handle_failure.assert_awaited_once()
        
    async def test_execute_with_fallback_success(self, circuit_breaker):
        async def test_func():
            return "success"
            
        result = await circuit_breaker.execute_with_fallback(
            test_func,
            cache_key="test"
        )
        
        assert result == "success"
        
    async def test_execute_with_fallback_failure(self,
                                               circuit_breaker,
                                               mock_cache):
        async def test_func():
            raise Exception("primary failed")
            
        async def fallback_func():
            return "fallback"
            
        circuit_breaker.add_fallback(fallback_func)
        mock_cache.get.return_value = None
        
        result = await circuit_breaker.execute_with_fallback(
            test_func,
            cache_key="test"
        )
        
        assert result == "fallback"
        
    async def test_execute_with_fallback_cached(self,
                                              circuit_breaker,
                                              mock_cache,
                                              mock_metrics):
        async def test_func():
            raise Exception("primary failed")
            
        mock_cache.get.return_value = "cached"
        
        result = await circuit_breaker.execute_with_fallback(
            test_func,
            cache_key="test"
        )
        
        assert result == "cached"
        mock_metrics.increment.assert_awaited_with(
            "circuit_breaker_fallback_success",
            {"service": "test_service"}
        )
        
    async def test_execute_with_fallback_all_fail(self,
                                                circuit_breaker,
                                                mock_cache):
        async def test_func():
            raise Exception("primary failed")
            
        async def fallback_func():
            raise Exception("fallback failed")
            
        circuit_breaker.add_fallback(fallback_func)
        mock_cache.get.return_value = None
        
        with pytest.raises(Exception) as exc:
            await circuit_breaker.execute_with_fallback(
                test_func,
                cache_key="test"
            )
            
        assert str(exc.value) == "primary failed"

class TestRecoveryPatternIntegration:
    @pytest.fixture
    def exponential_circuit_breaker(self, mock_cache, mock_metrics):
        return AdvancedCircuitBreaker(
            service_name="test_service",
            metrics=mock_metrics,
            cache=mock_cache,
            recovery_pattern=ExponentialBackoffPattern()
        )
        
    @pytest.fixture
    def partial_circuit_breaker(self, mock_cache, mock_metrics):
        return AdvancedCircuitBreaker(
            service_name="test_service",
            metrics=mock_metrics,
            cache=mock_cache,
            feature_priorities={
                "critical": 3,
                "important": 2,
                "optional": 1
            }
        )
        
    @pytest.fixture
    def adaptive_circuit_breaker(self, mock_cache, mock_metrics):
        return AdvancedCircuitBreaker(
            service_name="test_service",
            metrics=mock_metrics,
            cache=mock_cache,
            recovery_pattern=AdaptiveRecoveryPattern(mock_metrics)
        )
        
    async def test_exponential_backoff_recovery(self,
                                              exponential_circuit_breaker,
                                              mock_cache):
        mock_cache.get.return_value = CircuitState.OPEN.value
        
        # First attempt should be allowed
        allowed = await exponential_circuit_breaker.allow_request()
        assert allowed
        
        # Record failure to increment attempt counter
        await exponential_circuit_breaker.record_failure()
        
        # Second attempt should be blocked by backoff
        allowed = await exponential_circuit_breaker.allow_request()
        assert not allowed
        
    async def test_partial_recovery_features(self,
                                           partial_circuit_breaker,
                                           mock_metrics):
        # Simulate successful recovery
        partial_circuit_breaker.state = CircuitState.HALF_OPEN
        
        await partial_circuit_breaker.record_success()
        await partial_circuit_breaker.record_success()
        await partial_circuit_breaker.record_success()
        await partial_circuit_breaker.record_success()
        await partial_circuit_breaker.record_success()
        
        # Critical feature should be enabled
        assert "critical" in partial_circuit_breaker.recovery_pattern.enabled_features
        
    async def test_adaptive_recovery_metrics(self,
                                           adaptive_circuit_breaker,
                                           mock_metrics):
        mock_metrics.get_gauge.side_effect = [50.0, 60.0, 70.0]
        
        allowed = await adaptive_circuit_breaker.allow_request()
        assert allowed
        
        # Simulate successful recovery
        await adaptive_circuit_breaker.record_success()
        
        # Rate should increase
        assert adaptive_circuit_breaker.recovery_pattern.current_rate > 0.1 