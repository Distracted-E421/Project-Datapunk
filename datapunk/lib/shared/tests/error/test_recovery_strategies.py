import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from datapunk_shared.error.recovery_strategies import (
    RetryStrategy,
    CircuitBreakerStrategy,
    FallbackStrategy,
    ExponentialBackoffStrategy,
    BulkheadStrategy
)
from datapunk_shared.error.error_types import (
    ErrorSeverity,
    ErrorCategory,
    DatapunkError
)

@pytest.fixture
def mock_operation():
    return Mock()

@pytest.mark.asyncio
async def test_retry_with_exponential_backoff():
    strategy = ExponentialBackoffStrategy(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=1.0,
        multiplier=2.0
    )
    
    attempt_count = 0
    async def operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise DatapunkError("Temporary error")
        return "success"
    
    result = await strategy.execute(operation)
    assert result == "success"
    assert attempt_count == 3

@pytest.mark.asyncio
async def test_circuit_breaker_state_transitions():
    breaker = CircuitBreakerStrategy(
        failure_threshold=2,
        reset_timeout=0.1
    )
    
    # Test closed -> open transition
    for _ in range(2):
        with pytest.raises(DatapunkError):
            await breaker.execute(
                lambda: (_ for _ in ()).throw(DatapunkError("error"))
            )
    
    assert breaker.is_open()
    
    # Test open -> half-open transition
    await asyncio.sleep(0.2)  # Wait for reset timeout
    assert breaker.is_half_open()

@pytest.mark.asyncio
async def test_fallback_strategy():
    fallback = FallbackStrategy(
        fallback_value="default"
    )
    
    # Test primary operation failure
    async def failing_operation():
        raise DatapunkError("Primary failed")
    
    result = await fallback.execute(failing_operation)
    assert result == "default"
    
    # Test successful operation
    async def successful_operation():
        return "success"
    
    result = await fallback.execute(successful_operation)
    assert result == "success"

@pytest.mark.asyncio
async def test_bulkhead_isolation():
    bulkhead = BulkheadStrategy(
        max_concurrent=2,
        max_queue_size=1
    )
    
    # Test concurrent execution limit
    async def slow_operation():
        await asyncio.sleep(0.1)
        return "done"
    
    # Start max_concurrent operations
    tasks = [
        asyncio.create_task(bulkhead.execute(slow_operation))
        for _ in range(2)
    ]
    
    # Try to execute one more operation (should be queued)
    queued_task = asyncio.create_task(bulkhead.execute(slow_operation))
    
    # Try to execute another operation (should fail)
    with pytest.raises(DatapunkError):
        await bulkhead.execute(slow_operation)
    
    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, queued_task)
    assert all(result == "done" for result in results)

@pytest.mark.asyncio
async def test_retry_with_condition():
    strategy = RetryStrategy(
        max_attempts=3,
        delay_seconds=0.1,
        retry_if=lambda error: isinstance(error, DatapunkError)
    )
    
    # Test retry on matching error
    attempt_count = 0
    async def operation_with_matching_error():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise DatapunkError("Retry me")
        return "success"
    
    result = await strategy.execute(operation_with_matching_error)
    assert result == "success"
    
    # Test no retry on non-matching error
    with pytest.raises(ValueError):
        await strategy.execute(lambda: (_ for _ in ()).throw(ValueError()))

@pytest.mark.asyncio
async def test_circuit_breaker_metrics():
    breaker = CircuitBreakerStrategy(
        failure_threshold=2,
        reset_timeout=0.1
    )
    
    # Test metrics collection
    assert breaker.failure_count == 0
    assert breaker.success_count == 0
    
    # Record successful execution
    await breaker.execute(lambda: "success")
    assert breaker.success_count == 1
    
    # Record failed execution
    with pytest.raises(DatapunkError):
        await breaker.execute(
            lambda: (_ for _ in ()).throw(DatapunkError("error"))
        )
    assert breaker.failure_count == 1

@pytest.mark.asyncio
async def test_fallback_chain():
    primary_fallback = FallbackStrategy(fallback_value="primary_fallback")
    secondary_fallback = FallbackStrategy(fallback_value="secondary_fallback")
    
    async def operation():
        raise DatapunkError("All failed")
    
    # Test fallback chain
    result = await primary_fallback.execute(
        lambda: secondary_fallback.execute(operation)
    )
    assert result == "primary_fallback"

@pytest.mark.asyncio
async def test_recovery_strategy_composition():
    # Compose multiple strategies
    retry = RetryStrategy(max_attempts=2, delay_seconds=0.1)
    breaker = CircuitBreakerStrategy(failure_threshold=3, reset_timeout=0.1)
    fallback = FallbackStrategy(fallback_value="fallback")
    
    async def unreliable_operation():
        raise DatapunkError("Service unavailable")
    
    # Apply strategies in sequence
    result = await fallback.execute(
        lambda: breaker.execute(
            lambda: retry.execute(unreliable_operation)
        )
    )
    
    assert result == "fallback"  # Fallback should be used after retries fail 