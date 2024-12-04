"""Tests for context-aware retry management system"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
from datapunk_shared.mesh.circuit_breaker.context_retry import (
    RetryOutcome,
    ErrorCategory,
    RetryContext,
    RetryPolicy,
    ErrorClassifier,
    ExponentialBackoffStrategy,
    AdaptiveRetryStrategy,
    ContextRetryManager
)

@pytest.fixture
def retry_context():
    return RetryContext(
        error_type=TimeoutError,
        error_message="Connection timed out",
        attempt_number=1,
        elapsed_time_ms=100.0,
        resource_path="/api/resource",
        method="GET"
    )

@pytest.fixture
def retry_policy():
    return RetryPolicy(
        max_attempts=3,
        base_delay_ms=100.0,
        max_delay_ms=5000.0,
        jitter_factor=0.2
    )

@pytest.fixture
def error_classifier():
    return ErrorClassifier()

@pytest.fixture
def exponential_strategy():
    return ExponentialBackoffStrategy()

@pytest.fixture
def adaptive_strategy():
    return AdaptiveRetryStrategy()

@pytest.fixture
def metrics_client():
    return AsyncMock()

class TestErrorClassifier:
    def test_classify_timeout(self, error_classifier):
        error = TimeoutError("Connection timed out")
        assert error_classifier.classify(error) == ErrorCategory.TIMEOUT

    def test_classify_rate_limit(self, error_classifier):
        error = RuntimeError("Rate limit exceeded")
        assert error_classifier.classify(error) == ErrorCategory.RATE_LIMIT

    def test_classify_resource_exhausted(self, error_classifier):
        error = RuntimeError("Resource exhausted")
        assert error_classifier.classify(error) == ErrorCategory.RESOURCE_EXHAUSTED

    def test_classify_unknown(self, error_classifier):
        error = Exception("Unknown error")
        assert error_classifier.classify(error) == ErrorCategory.UNKNOWN

class TestExponentialBackoffStrategy:
    def test_should_retry_within_limits(self, exponential_strategy, retry_context, retry_policy):
        outcome = exponential_strategy.should_retry(retry_context, retry_policy)
        assert outcome == RetryOutcome.RETRY

    def test_should_not_retry_exceeded_attempts(self, exponential_strategy, retry_context, retry_policy):
        retry_context.attempt_number = 4
        outcome = exponential_strategy.should_retry(retry_context, retry_policy)
        assert outcome == RetryOutcome.FAIL_FAST

    def test_delay_increases_exponentially(self, exponential_strategy, retry_context, retry_policy):
        retry_policy.jitter_factor = 0  # Disable jitter for predictable testing
        
        delays = []
        for i in range(1, 4):
            retry_context.attempt_number = i
            delay = exponential_strategy.get_delay_ms(retry_context, retry_policy)
            delays.append(delay)
            
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]
        assert abs(delays[1] / delays[0] - 2.0) < 0.01

    def test_respects_max_delay(self, exponential_strategy, retry_context, retry_policy):
        retry_context.attempt_number = 10
        delay = exponential_strategy.get_delay_ms(retry_context, retry_policy)
        assert delay <= retry_policy.max_delay_ms

class TestAdaptiveRetryStrategy:
    def test_should_retry_retryable_error(self, adaptive_strategy, retry_context, retry_policy):
        outcome = adaptive_strategy.should_retry(retry_context, retry_policy)
        assert outcome == RetryOutcome.RETRY

    def test_should_not_retry_non_retryable_error(self, adaptive_strategy, retry_context, retry_policy):
        retry_context.error_type = ValueError
        retry_context.error_message = "Invalid input"
        outcome = adaptive_strategy.should_retry(retry_context, retry_policy)
        assert outcome == RetryOutcome.FAIL_FAST

    def test_detects_rate_limiting(self, adaptive_strategy, retry_context, retry_policy):
        # Simulate multiple rate limit errors
        for _ in range(3):
            retry_context.error_message = "Rate limit exceeded"
            adaptive_strategy.should_retry(retry_context, retry_policy)
            
        outcome = adaptive_strategy.should_retry(retry_context, retry_policy)
        assert outcome == RetryOutcome.BACKOFF

    def test_detects_resource_exhaustion(self, adaptive_strategy, retry_context, retry_policy):
        # Simulate resource exhaustion errors
        for _ in range(2):
            retry_context.error_message = "Resource exhausted"
            adaptive_strategy.should_retry(retry_context, retry_policy)
            
        outcome = adaptive_strategy.should_retry(retry_context, retry_policy)
        assert outcome == RetryOutcome.REDIRECT

    def test_error_history_cleanup(self, adaptive_strategy, retry_context, retry_policy):
        # Add old errors
        old_time = datetime.utcnow() - timedelta(minutes=10)
        adaptive_strategy.error_history = [
            (old_time, ErrorCategory.TIMEOUT),
            (old_time, ErrorCategory.RATE_LIMIT)
        ]
        
        adaptive_strategy.should_retry(retry_context, retry_policy)
        
        # Only the new error should remain
        assert len(adaptive_strategy.error_history) == 1

class TestContextRetryManager:
    @pytest.mark.asyncio
    async def test_should_retry_success(self, retry_context, metrics_client):
        manager = ContextRetryManager(metrics_client=metrics_client)
        should_retry, delay = await manager.should_retry(retry_context)
        assert should_retry
        assert delay > 0

    @pytest.mark.asyncio
    async def test_should_not_retry_exceeded_attempts(self, retry_context, metrics_client):
        manager = ContextRetryManager(metrics_client=metrics_client)
        retry_context.attempt_number = 10
        should_retry, delay = await manager.should_retry(retry_context)
        assert not should_retry
        assert delay == 0.0

    @pytest.mark.asyncio
    async def test_metrics_recording(self, retry_context, metrics_client):
        manager = ContextRetryManager(metrics_client=metrics_client)
        await manager.should_retry(retry_context)
        
        assert metrics_client.increment.called
        assert metrics_client.gauge.called

    def test_get_retry_metrics(self, retry_context):
        manager = ContextRetryManager()
        manager.should_retry(retry_context)
        
        metrics = manager.get_retry_metrics()
        assert "error_counts" in metrics
        assert "total_errors" in metrics
        assert metrics["total_errors"] > 0

    @pytest.mark.asyncio
    async def test_priority_handling(self, retry_context, metrics_client):
        manager = ContextRetryManager(metrics_client=metrics_client)
        retry_context.priority = "HIGH"
        should_retry, delay = await manager.should_retry(retry_context)
        assert should_retry
        
        retry_context.priority = "LOW"
        retry_context.attempt_number = 2
        should_retry, delay = await manager.should_retry(retry_context)
        assert not should_retry

    @pytest.mark.asyncio
    async def test_method_specific_behavior(self, retry_context, metrics_client):
        manager = ContextRetryManager(metrics_client=metrics_client)
        
        # Test GET method
        retry_context.method = "GET"
        retry_context.attempt_number = 4
        should_retry, _ = await manager.should_retry(retry_context)
        assert should_retry
        
        # Test DELETE method
        retry_context.method = "DELETE"
        retry_context.attempt_number = 2
        should_retry, _ = await manager.should_retry(retry_context)
        assert not should_retry 