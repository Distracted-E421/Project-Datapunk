import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.routing import (
    RetryHandler,
    RetryConfig,
    BackoffStrategy,
    RetryError,
    RetryContext
)

@pytest.fixture
def retry_config():
    return RetryConfig(
        max_attempts=3,
        initial_delay=0.1,
        max_delay=1.0,
        backoff_factor=2.0,
        jitter=0.1
    )

@pytest.fixture
def retry_handler(retry_config):
    return RetryHandler(config=retry_config)

@pytest.fixture
def sample_operation():
    async def operation():
        return "success"
    return operation

@pytest.mark.asyncio
async def test_retry_initialization(retry_handler, retry_config):
    assert retry_handler.config == retry_config
    assert retry_handler.attempts == 0
    assert retry_handler.last_attempt_time is None

@pytest.mark.asyncio
async def test_successful_operation(retry_handler, sample_operation):
    result = await retry_handler.execute(sample_operation)
    assert result == "success"
    assert retry_handler.attempts == 1

@pytest.mark.asyncio
async def test_retry_with_failure():
    handler = RetryHandler(RetryConfig(max_attempts=3))
    
    attempt_count = 0
    async def failing_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError("Temporary failure")
        return "success"
    
    result = await handler.execute(failing_operation)
    assert result == "success"
    assert handler.attempts == 3

@pytest.mark.asyncio
async def test_max_attempts_exceeded():
    handler = RetryHandler(RetryConfig(max_attempts=2))
    
    async def always_fails():
        raise ValueError("Persistent failure")
    
    with pytest.raises(RetryError) as exc_info:
        await handler.execute(always_fails)
    
    assert handler.attempts == 2
    assert "max attempts exceeded" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_exponential_backoff():
    handler = RetryHandler(RetryConfig(
        max_attempts=3,
        initial_delay=0.1,
        backoff_strategy=BackoffStrategy.EXPONENTIAL
    ))
    
    delays = []
    async def failing_operation():
        if handler.attempts > 0:
            delays.append(
                (datetime.utcnow() - handler.last_attempt_time).total_seconds()
            )
        raise ValueError("Failure")
    
    with pytest.raises(RetryError):
        await handler.execute(failing_operation)
    
    # Each delay should be roughly double the previous
    assert delays[1] > delays[0] * 1.8

@pytest.mark.asyncio
async def test_linear_backoff():
    handler = RetryHandler(RetryConfig(
        max_attempts=3,
        initial_delay=0.1,
        backoff_strategy=BackoffStrategy.LINEAR
    ))
    
    delays = []
    async def failing_operation():
        if handler.attempts > 0:
            delays.append(
                (datetime.utcnow() - handler.last_attempt_time).total_seconds()
            )
        raise ValueError("Failure")
    
    with pytest.raises(RetryError):
        await handler.execute(failing_operation)
    
    # Delays should increase linearly
    diff1 = delays[1] - delays[0]
    diff2 = delays[1] - delays[0]
    assert abs(diff1 - diff2) < 0.05

@pytest.mark.asyncio
async def test_retry_with_jitter(retry_handler):
    delays = set()
    
    async def failing_operation():
        if retry_handler.attempts > 0:
            delays.add(
                (datetime.utcnow() - retry_handler.last_attempt_time).total_seconds()
            )
        raise ValueError("Failure")
    
    with pytest.raises(RetryError):
        await retry_handler.execute(failing_operation)
    
    # With jitter, delays should vary
    assert len(delays) > 1

@pytest.mark.asyncio
async def test_retry_condition():
    async def should_retry(error, context):
        return isinstance(error, ValueError)
    
    handler = RetryHandler(
        RetryConfig(max_attempts=2),
        retry_condition=should_retry
    )
    
    # Should retry ValueError
    with pytest.raises(RetryError):
        await handler.execute(lambda: (_ for _ in ()).throw(ValueError()))
    assert handler.attempts == 2
    
    # Should not retry TypeError
    with pytest.raises(TypeError):
        await handler.execute(lambda: (_ for _ in ()).throw(TypeError()))
    assert handler.attempts == 1

@pytest.mark.asyncio
async def test_retry_context(retry_handler):
    context = RetryContext(
        operation_name="test_op",
        attempt=1,
        error=None,
        metadata={"important": True}
    )
    
    async def operation_with_context():
        assert retry_handler.context.operation_name == "test_op"
        assert retry_handler.context.metadata["important"] is True
        return "success"
    
    result = await retry_handler.execute(
        operation_with_context,
        context=context
    )
    assert result == "success"

@pytest.mark.asyncio
async def test_retry_metrics(retry_handler):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        async def failing_operation():
            raise ValueError("Failure")
        
        with pytest.raises(RetryError):
            await retry_handler.execute(failing_operation)
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_histogram.assert_called()

@pytest.mark.asyncio
async def test_retry_events(retry_handler):
    events = []
    
    def event_handler(event_type, context):
        events.append((event_type, context))
    
    retry_handler.on_retry_event(event_handler)
    
    async def failing_operation():
        raise ValueError("Failure")
    
    with pytest.raises(RetryError):
        await retry_handler.execute(failing_operation)
    
    assert len(events) > 0
    assert events[0][0] == "retry_attempt"

@pytest.mark.asyncio
async def test_retry_timeout():
    handler = RetryHandler(RetryConfig(
        max_attempts=2,
        timeout_seconds=0.1
    ))
    
    async def slow_operation():
        await asyncio.sleep(0.2)
        return "success"
    
    with pytest.raises(asyncio.TimeoutError):
        await handler.execute(slow_operation)

@pytest.mark.asyncio
async def test_concurrent_retries(retry_handler):
    async def failing_operation():
        raise ValueError("Failure")
    
    # Execute multiple retries concurrently
    tasks = [
        retry_handler.execute(failing_operation)
        for _ in range(3)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    assert all(isinstance(r, RetryError) for r in results)

@pytest.mark.asyncio
async def test_retry_state_persistence(retry_handler):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        await retry_handler.save_state()
        mock_file.write.assert_called_once()
        
        await retry_handler.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_custom_backoff_strategy():
    def custom_backoff(attempt, initial_delay):
        return initial_delay * attempt * 0.5
    
    handler = RetryHandler(
        RetryConfig(max_attempts=3, initial_delay=0.1),
        backoff_strategy=custom_backoff
    )
    
    delays = []
    async def failing_operation():
        if handler.attempts > 0:
            delays.append(
                (datetime.utcnow() - handler.last_attempt_time).total_seconds()
            )
        raise ValueError("Failure")
    
    with pytest.raises(RetryError):
        await handler.execute(failing_operation)
    
    # Verify custom backoff was applied
    assert 0.05 <= delays[0] <= 0.15  # attempt 1: 0.1 * 1 * 0.5
    assert 0.1 <= delays[1] <= 0.2    # attempt 2: 0.1 * 2 * 0.5