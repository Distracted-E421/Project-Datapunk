import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from datapunk_shared.mesh.retry import (
    RetryStrategy,
    ExponentialBackoff,
    LinearBackoff,
    RetryConfig,
    RetryError
)

@pytest.fixture
def retry_config():
    return RetryConfig(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=1.0,
        jitter=0.1
    )

@pytest.fixture
def exponential_backoff(retry_config):
    return ExponentialBackoff(config=retry_config)

@pytest.fixture
def linear_backoff(retry_config):
    return LinearBackoff(config=retry_config)

@pytest.mark.asyncio
async def test_exponential_backoff_delays(exponential_backoff):
    delays = [
        await exponential_backoff.get_delay(attempt)
        for attempt in range(3)
    ]
    
    # Each delay should be roughly double the previous
    assert delays[1] > delays[0] * 1.8  # Allow for jitter
    assert delays[2] > delays[1] * 1.8

@pytest.mark.asyncio
async def test_linear_backoff_delays(linear_backoff):
    delays = [
        await linear_backoff.get_delay(attempt)
        for attempt in range(3)
    ]
    
    # Delays should increase linearly
    diff1 = delays[1] - delays[0]
    diff2 = delays[2] - delays[1]
    assert abs(diff1 - diff2) < 0.05  # Allow for jitter

@pytest.mark.asyncio
async def test_retry_with_success():
    async def operation():
        return "success"
    
    strategy = RetryStrategy(RetryConfig(max_attempts=3))
    result = await strategy.execute(operation)
    assert result == "success"

@pytest.mark.asyncio
async def test_retry_with_eventual_success():
    attempt_count = 0
    
    async def operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise Exception("Temporary failure")
        return "success"
    
    strategy = RetryStrategy(RetryConfig(max_attempts=3))
    result = await strategy.execute(operation)
    
    assert result == "success"
    assert attempt_count == 3

@pytest.mark.asyncio
async def test_retry_max_attempts_exceeded():
    async def operation():
        raise Exception("Persistent failure")
    
    strategy = RetryStrategy(RetryConfig(max_attempts=3))
    
    with pytest.raises(RetryError):
        await strategy.execute(operation)

@pytest.mark.asyncio
async def test_retry_with_custom_predicate():
    async def operation():
        raise ValueError("Special error")
    
    def retry_predicate(error):
        return isinstance(error, ValueError)
    
    strategy = RetryStrategy(
        RetryConfig(max_attempts=3),
        should_retry=retry_predicate
    )
    
    with pytest.raises(RetryError):
        await strategy.execute(operation)

@pytest.mark.asyncio
async def test_retry_with_timeout():
    async def slow_operation():
        await asyncio.sleep(0.2)
        return "success"
    
    strategy = RetryStrategy(
        RetryConfig(
            max_attempts=3,
            timeout_seconds=0.1
        )
    )
    
    with pytest.raises(asyncio.TimeoutError):
        await strategy.execute(slow_operation)

@pytest.mark.asyncio
async def test_retry_with_jitter(exponential_backoff):
    delays = set()
    for _ in range(10):
        delay = await exponential_backoff.get_delay(1)
        delays.add(delay)
    
    # With jitter, delays should vary
    assert len(delays) > 1

@pytest.mark.asyncio
async def test_retry_callback_notification():
    attempt_count = 0
    callback_count = 0
    
    async def operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise Exception("Temporary failure")
        return "success"
    
    async def on_retry(attempt, error, next_delay):
        nonlocal callback_count
        callback_count += 1
    
    strategy = RetryStrategy(
        RetryConfig(max_attempts=3),
        on_retry=on_retry
    )
    
    result = await strategy.execute(operation)
    assert result == "success"
    assert callback_count == 2  # Called twice for the two retries

@pytest.mark.asyncio
async def test_retry_state_tracking():
    attempt_count = 0
    
    async def operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise Exception("Temporary failure")
        return "success"
    
    strategy = RetryStrategy(RetryConfig(max_attempts=3))
    result = await strategy.execute(operation)
    
    assert strategy.last_attempt_time is not None
    assert strategy.total_attempts == 3
    assert strategy.total_delay > 0

@pytest.mark.asyncio
async def test_retry_with_circuit_breaker_integration():
    circuit_breaker = Mock()
    circuit_breaker.is_closed = AsyncMock(return_value=True)
    circuit_breaker.record_success = AsyncMock()
    circuit_breaker.record_failure = AsyncMock()
    
    async def operation():
        return "success"
    
    strategy = RetryStrategy(
        RetryConfig(max_attempts=3),
        circuit_breaker=circuit_breaker
    )
    
    result = await strategy.execute(operation)
    assert result == "success"
    circuit_breaker.record_success.assert_called_once() 