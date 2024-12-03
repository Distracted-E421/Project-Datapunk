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
from datapunk_shared.mesh.circuit_breaker.request_priority import (
    RequestPriority,
    PriorityConfig,
    PriorityManager
)
from datapunk_shared.exceptions import CircuitBreakerError
import asyncio

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
def priority_config():
    return PriorityConfig(
        min_priority=RequestPriority.LOW.value,
        reserved_slots={
            RequestPriority.CRITICAL: 2,
            RequestPriority.HIGH: 4,
            RequestPriority.NORMAL: 8
        }
    )

@pytest.fixture
def circuit_breaker(mock_cache, mock_metrics, mock_recovery_pattern, priority_config):
    return AdvancedCircuitBreaker(
        service_name="test_service",
        metrics=mock_metrics,
        cache=mock_cache,
        recovery_pattern=mock_recovery_pattern,
        priority_config=priority_config
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
        mock_metrics.increment.assert_awaited_with(
            "circuit_breaker_rejections",
            {"service": "test_service"}
        )
        
    async def test_execute_with_priority(self, circuit_breaker):
        async def test_func():
            return "success"
            
        result = await circuit_breaker.execute_with_fallback(
            test_func,
            priority=RequestPriority.HIGH
        )
        
        assert result == "success"
        
    async def test_execute_below_min_priority(self, circuit_breaker):
        async def test_func():
            return "success"
            
        circuit_breaker.priority_manager.config.min_priority = RequestPriority.HIGH.value
        
        with pytest.raises(CircuitBreakerError) as exc:
            await circuit_breaker.execute_with_fallback(
                test_func,
                priority=RequestPriority.LOW
            )
            
        assert "Request rejected" in str(exc.value)
        
    async def test_execute_with_timeout(self, circuit_breaker):
        async def test_func():
            return "success"
            
        # Set very short timeout
        timeout_ms = 1
        
        with pytest.raises(CircuitBreakerError):
            await circuit_breaker.execute_with_fallback(
                test_func,
                priority=RequestPriority.NORMAL,
                timeout_ms=timeout_ms
            )
            
    async def test_priority_adjustment_on_failure(self,
                                                circuit_breaker,
                                                mock_metrics):
        await circuit_breaker.record_failure()
        await circuit_breaker.record_failure()
        await circuit_breaker.record_failure()
        await circuit_breaker.record_failure()
        await circuit_breaker.record_failure()
        
        # Verify priority threshold was raised
        assert circuit_breaker.priority_manager.config.min_priority == \
               RequestPriority.HIGH.value
               
    async def test_priority_reset_on_recovery(self,
                                            circuit_breaker,
                                            mock_recovery_pattern):
        # Set initial high threshold
        await circuit_breaker.priority_manager.adjust_min_priority(
            RequestPriority.HIGH.value
        )
        
        # Simulate successful recovery
        circuit_breaker.state = CircuitState.HALF_OPEN
        mock_recovery_pattern.handle_success.return_value = True
        
        await circuit_breaker.record_success()
        
        # Verify threshold was reset
        assert circuit_breaker.priority_manager.config.min_priority == 0
        
    async def test_critical_priority_bypass(self, circuit_breaker, mock_cache):
        mock_cache.get.return_value = CircuitState.OPEN.value
        
        # Critical requests should bypass circuit breaker
        result = await circuit_breaker.execute_with_fallback(
            lambda: "critical",
            priority=RequestPriority.CRITICAL
        )
        
        assert result == "critical"
        
    async def test_resource_reservation(self, circuit_breaker):
        priority = RequestPriority.HIGH
        slots = circuit_breaker.priority_manager.config.reserved_slots[priority]
        
        # Fill up reserved slots
        tasks = []
        for _ in range(slots):
            tasks.append(
                circuit_breaker.execute_with_fallback(
                    lambda: "success",
                    priority=priority
                )
            )
            
        # Additional request should be rejected
        with pytest.raises(CircuitBreakerError):
            await circuit_breaker.execute_with_fallback(
                lambda: "fail",
                priority=priority
            )
            
    async def test_request_cleanup(self, circuit_breaker):
        priority = RequestPriority.NORMAL
        
        # Start request
        await circuit_breaker.execute_with_fallback(
            lambda: "success",
            priority=priority
        )
        
        # Verify request was cleaned up
        assert circuit_breaker.priority_manager.get_active_requests(priority) == 0
        
    async def test_metrics_recording(self,
                                   circuit_breaker,
                                   mock_metrics):
        await circuit_breaker.execute_with_fallback(
            lambda: "success",
            priority=RequestPriority.HIGH
        )
        
        # Verify priority metrics were recorded
        mock_metrics.increment.assert_any_call(
            "circuit_breaker_priority_check",
            {"priority": "HIGH"}
        )

@pytest.mark.asyncio
class TestAdvancedCircuitBreakerFailurePrediction:
    async def test_metrics_update(self, circuit_breaker):
        # Make some requests
        for _ in range(5):
            await circuit_breaker.before_request()
            await circuit_breaker.after_request()
            
        # Force metrics update
        circuit_breaker.last_metrics_update = (
            datetime.utcnow() - timedelta(seconds=11)
        )
        await circuit_breaker._update_metrics()
        
        # Verify metrics were recorded
        circuit_breaker.metrics.gauge.assert_called()
        
    async def test_latency_recording(self, circuit_breaker):
        await circuit_breaker.before_request()
        # Simulate request time
        await asyncio.sleep(0.1)
        await circuit_breaker.after_request()
        
        # Verify latency was recorded
        calls = circuit_breaker.metrics.gauge.call_args_list
        latency_calls = [
            call for call in calls
            if "latency" in call[0][0]
        ]
        assert len(latency_calls) > 0
        
    async def test_error_rate_recording(self, circuit_breaker):
        # Make some requests with failures
        for _ in range(5):
            await circuit_breaker.before_request()
            await circuit_breaker.on_failure(Exception("test"))
            
        # Force metrics update
        circuit_breaker.last_metrics_update = (
            datetime.utcnow() - timedelta(seconds=11)
        )
        await circuit_breaker._update_metrics()
        
        # Verify error rate was recorded
        calls = circuit_breaker.metrics.gauge.call_args_list
        error_calls = [
            call for call in calls
            if "error_rate" in call[0][0]
        ]
        assert len(error_calls) > 0
        
    async def test_predicted_failure_opens_circuit(self, circuit_breaker):
        # Mock failure prediction
        async def mock_predict():
            return True, 0.9  # High confidence failure prediction
            
        circuit_breaker.failure_predictor.predict_failure = mock_predict
        
        # Verify circuit opens on predicted failure
        with pytest.raises(CircuitBreakerError) as exc:
            await circuit_breaker.before_request()
            
        assert "predicted failure" in str(exc.value)
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Verify metrics
        circuit_breaker.metrics.increment.assert_called_with(
            "circuit_breaker_state_change",
            {"from": "closed", "to": "open",
             "reason": "predicted_failure"}
        )
        
    async def test_low_confidence_prediction_keeps_circuit_closed(
            self, circuit_breaker):
        # Mock low confidence prediction
        async def mock_predict():
            return True, 0.3  # Low confidence
            
        circuit_breaker.failure_predictor.predict_failure = mock_predict
        
        # Verify circuit stays closed
        await circuit_breaker.before_request()
        assert circuit_breaker.state == CircuitState.CLOSED
        
    async def test_dynamic_thresholds_update(self, circuit_breaker):
        # Make requests to generate metrics
        for _ in range(10):
            await circuit_breaker.before_request()
            if _ % 3 == 0:  # Some failures
                await circuit_breaker.on_failure(Exception("test"))
            else:
                await circuit_breaker.after_request()
                
        # Force threshold update
        circuit_breaker.last_metrics_update = (
            datetime.utcnow() - timedelta(seconds=11)
        )
        await circuit_breaker._update_metrics()
        
        # Verify thresholds were updated
        predictor = circuit_breaker.failure_predictor
        assert predictor.thresholds[PredictionMetric.REQUEST_RATE] is not None

@pytest.mark.asyncio
class TestAdvancedCircuitBreakerTimeout:
    async def test_timeout_initialization(self, circuit_breaker):
        assert circuit_breaker.timeout_manager is not None
        assert circuit_breaker.timeout_manager.current_timeout_ms > 0
        
    async def test_timeout_before_request(self, circuit_breaker):
        timeout = await circuit_breaker.before_request()
        
        assert timeout is not None
        assert timeout >= circuit_breaker.timeout_manager.config.min_timeout_ms
        assert timeout <= circuit_breaker.timeout_manager.config.max_timeout_ms
        
    async def test_timeout_adjustment_after_success(self, circuit_breaker):
        initial_timeout = await circuit_breaker.before_request()
        await asyncio.sleep(0.1)  # Simulate request time
        await circuit_breaker.after_request()
        
        # Record more successful requests
        for _ in range(5):
            await circuit_breaker.before_request()
            await asyncio.sleep(0.05)  # Faster responses
            await circuit_breaker.after_request()
            
        new_timeout = await circuit_breaker.before_request()
        
        # Timeout should adapt to faster response times
        assert new_timeout < initial_timeout
        
    async def test_timeout_adjustment_after_failures(self, circuit_breaker):
        initial_timeout = await circuit_breaker.before_request()
        
        # Simulate timeout failures
        for _ in range(3):
            await circuit_breaker.before_request()
            await circuit_breaker.on_failure(TimeoutError())
            
        new_timeout = await circuit_breaker.before_request()
        
        # Timeout should increase after failures
        assert new_timeout > initial_timeout
        
    async def test_timeout_metrics_reporting(self, circuit_breaker):
        # Generate some timeout data
        await circuit_breaker.before_request()
        await asyncio.sleep(0.1)
        await circuit_breaker.after_request()
        
        metrics = await circuit_breaker.get_metrics()
        
        # Verify timeout metrics are included
        assert "timeout_current_timeout" in metrics
        assert "timeout_success_rate" in metrics
        assert "timeout_mean_response_time" in metrics
        
    async def test_timeout_strategy_behavior(self, circuit_breaker):
        # Test percentile strategy
        circuit_breaker.timeout_manager.config.strategy = TimeoutStrategy.PERCENTILE
        
        # Add consistent response times
        for _ in range(5):
            await circuit_breaker.before_request()
            await asyncio.sleep(0.1)
            await circuit_breaker.after_request()
            
        percentile_timeout = await circuit_breaker.before_request()
        
        # Test adaptive strategy
        circuit_breaker.timeout_manager.config.strategy = TimeoutStrategy.ADAPTIVE
        
        # Add some failures
        for _ in range(2):
            await circuit_breaker.before_request()
            await circuit_breaker.on_failure(TimeoutError())
            
        adaptive_timeout = await circuit_breaker.before_request()
        
        # Adaptive should be higher due to failures
        assert adaptive_timeout > percentile_timeout
        
    async def test_timeout_integration_with_circuit_state(self, circuit_breaker):
        # Fill failure count to near threshold
        for _ in range(circuit_breaker.failure_threshold - 1):
            await circuit_breaker.before_request()
            await circuit_breaker.on_failure(TimeoutError())
            
        # Verify circuit stays closed but timeout increases
        initial_timeout = await circuit_breaker.before_request()
        assert circuit_breaker.state == CircuitState.CLOSED
        
        # One more timeout failure
        await circuit_breaker.on_failure(TimeoutError())
        
        # Circuit should open and timeout should be high
        with pytest.raises(CircuitBreakerError):
            await circuit_breaker.before_request()
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Wait for reset
        await asyncio.sleep(0.1)
        circuit_breaker.last_failure_time = (
            datetime.utcnow() - timedelta(seconds=61)
        )
        
        # Should enter half-open with adjusted timeout
        timeout = await circuit_breaker.before_request()
        assert circuit_breaker.state == CircuitState.HALF_OPEN
        assert timeout > initial_timeout  # Timeout should be higher

@pytest.mark.asyncio
class TestAdvancedCircuitBreakerPartialRecovery:
    @pytest.fixture
    def feature_configs(self):
        return {
            "auth": FeatureConfig(
                name="auth",
                priority=1,
                dependencies=set(),
                required=True
            ),
            "api": FeatureConfig(
                name="api",
                priority=2,
                dependencies={"auth"}
            )
        }
        
    @pytest.fixture
    def circuit_breaker_with_features(self, mock_metrics, feature_configs):
        return AdvancedCircuitBreaker(
            metrics_client=mock_metrics,
            features=feature_configs
        )
        
    async def test_initialization_with_features(self, circuit_breaker_with_features):
        assert circuit_breaker_with_features.recovery_manager is not None
        assert len(circuit_breaker_with_features.recovery_manager.features) == 2
        
    async def test_feature_unavailable(self, circuit_breaker_with_features):
        with pytest.raises(CircuitBreakerError) as exc:
            await circuit_breaker_with_features.before_request("api")
            
        assert "not available" in str(exc.value)
        
    async def test_feature_dependency_chain(self, circuit_breaker_with_features):
        # Enable auth feature
        await circuit_breaker_with_features.before_request("auth")
        await circuit_breaker_with_features.after_request("auth")
        
        # Fast forward test duration
        manager = circuit_breaker_with_features.recovery_manager
        auth_status = manager.status["auth"]
        auth_status.last_test_start = (
            datetime.utcnow() - 
            timedelta(seconds=auth_status.config.test_duration_seconds + 1)
        )
        
        # Complete auth test successfully
        for _ in range(10):
            await circuit_breaker_with_features.before_request("auth")
            await circuit_breaker_with_features.after_request("auth")
            
        # Now API should be available for testing
        await circuit_breaker_with_features.before_request("api")
        assert manager.status["api"].state == FeatureState.TESTING
        
    async def test_feature_failure_tracking(self, circuit_breaker_with_features):
        await circuit_breaker_with_features.before_request("auth")
        
        # Record some failures
        for _ in range(3):
            await circuit_breaker_with_features.on_failure(
                Exception("test"),
                feature="auth"
            )
            
        manager = circuit_breaker_with_features.recovery_manager
        auth_status = manager.status["auth"]
        assert auth_status.error_count == 3
        assert auth_status.health == FeatureHealth.UNHEALTHY
        
    async def test_required_feature_failure(self, circuit_breaker_with_features):
        await circuit_breaker_with_features.before_request("auth")
        
        # Make auth unhealthy
        for _ in range(10):
            await circuit_breaker_with_features.on_failure(
                Exception("test"),
                feature="auth"
            )
            
        # Fast forward test duration
        manager = circuit_breaker_with_features.recovery_manager
        auth_status = manager.status["auth"]
        auth_status.last_test_start = (
            datetime.utcnow() - 
            timedelta(seconds=auth_status.config.test_duration_seconds + 1)
        )
        
        # One more failure to trigger test completion
        await circuit_breaker_with_features.on_failure(
            Exception("test"),
            feature="auth"
        )
        
        # All features should be disabled
        for status in manager.status.values():
            assert status.state == FeatureState.DISABLED
            
    async def test_partial_recovery_metrics(self, circuit_breaker_with_features):
        # Add some test data
        await circuit_breaker_with_features.before_request("auth")
        
        for _ in range(8):
            await circuit_breaker_with_features.after_request("auth")
            
        for _ in range(2):
            await circuit_breaker_with_features.on_failure(
                Exception("test"),
                feature="auth"
            )
            
        metrics = await circuit_breaker_with_features.get_metrics()
        
        # Verify feature metrics are included
        assert "feature_auth" in metrics
        auth_metrics = metrics["feature_auth"]
        assert auth_metrics["success_count"] == 8
        assert auth_metrics["error_count"] == 2
        
    async def test_recovery_on_half_open(self, circuit_breaker_with_features):
        # Open circuit
        for _ in range(circuit_breaker_with_features.failure_threshold):
            await circuit_breaker_with_features.on_failure(Exception("test"))
            
        assert circuit_breaker_with_features.state == CircuitState.OPEN
        
        # Wait for reset timeout
        circuit_breaker_with_features.last_failure_time = (
            datetime.utcnow() - timedelta(seconds=61)
        )
        
        # Enter half-open state
        await circuit_breaker_with_features.before_request()
        
        # Verify recovery started
        manager = circuit_breaker_with_features.recovery_manager
        assert manager.recovery_start_time is not None
        assert manager.recovery_phase == 1
        
    async def test_feature_timeout_integration(self, circuit_breaker_with_features):
        await circuit_breaker_with_features.before_request("auth")
        
        # Record timeout failures
        for _ in range(3):
            await circuit_breaker_with_features.on_failure(
                TimeoutError(),
                feature="auth"
            )
            
        # Verify both timeout and feature metrics updated
        timeout = await circuit_breaker_with_features.timeout_manager.get_timeout()
        assert timeout > circuit_breaker_with_features.timeout_manager.config.initial_timeout_ms
        
        manager = circuit_breaker_with_features.recovery_manager
        auth_status = manager.status["auth"]
        assert auth_status.error_count == 3