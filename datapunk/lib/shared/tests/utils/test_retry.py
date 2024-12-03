import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.utils.retry import (
    RetryHandler,
    RetryConfig,
    RetryStrategy,
    RetryResult,
    RetryError
)

@pytest.fixture
def retry_config():
    return RetryConfig(
        name="test_retry",
        max_attempts=3,
        initial_delay=0.1,  # seconds
        max_delay=1.0,  # seconds
        backoff_factor=2.0,
        jitter=0.1,
        retry_exceptions=[
            ValueError,
            ConnectionError
        ],
        ignore_exceptions=[
            KeyError
        ],
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        metrics_enabled=True
    )

@pytest.fixture
async def retry_handler(retry_config):
    handler = RetryHandler(retry_config)
    await handler.initialize()
    return handler

@pytest.mark.asyncio
async def test_handler_initialization(retry_handler, retry_config):
    """Test retry handler initialization"""
    assert retry_handler.config == retry_config
    assert retry_handler.is_initialized
    assert retry_handler.attempts == 0

@pytest.mark.asyncio
async def test_successful_operation(retry_handler):
    """Test successful operation without retries"""
    async def success_operation():
        return "success"
    
    result = await retry_handler.execute(success_operation)
    
    assert result == "success"
    assert retry_handler.attempts == 1

@pytest.mark.asyncio
async def test_retry_on_exception(retry_handler):
    """Test retry on specified exception"""
    mock_operation = AsyncMock(side_effect=[
        ValueError("First attempt"),
        ValueError("Second attempt"),
        "success"
    ])
    
    result = await retry_handler.execute(mock_operation)
    
    assert result == "success"
    assert retry_handler.attempts == 3
    assert mock_operation.call_count == 3

@pytest.mark.asyncio
async def test_max_retries_exceeded(retry_handler):
    """Test max retries exceeded"""
    mock_operation = AsyncMock(side_effect=ValueError("Error"))
    
    with pytest.raises(RetryError) as exc_info:
        await retry_handler.execute(mock_operation)
    
    assert retry_handler.attempts == retry_handler.config.max_attempts
    assert "Max retries exceeded" in str(exc_info.value)

@pytest.mark.asyncio
async def test_ignore_exceptions(retry_handler):
    """Test ignored exceptions"""
    mock_operation = AsyncMock(side_effect=KeyError("Ignored error"))
    
    with pytest.raises(KeyError):
        await retry_handler.execute(mock_operation)
    
    assert retry_handler.attempts == 1  # No retries for ignored exception

@pytest.mark.asyncio
async def test_exponential_backoff(retry_handler):
    """Test exponential backoff strategy"""
    start_time = datetime.now()
    
    mock_operation = AsyncMock(side_effect=[
        ValueError("First attempt"),
        ValueError("Second attempt"),
        "success"
    ])
    
    result = await retry_handler.execute(mock_operation)
    
    duration = (datetime.now() - start_time).total_seconds()
    expected_min_duration = retry_handler.config.initial_delay + \
                          (retry_handler.config.initial_delay * retry_handler.config.backoff_factor)
    
    assert result == "success"
    assert duration >= expected_min_duration

@pytest.mark.asyncio
async def test_linear_backoff(retry_handler):
    """Test linear backoff strategy"""
    retry_handler.config.strategy = RetryStrategy.LINEAR_BACKOFF
    start_time = datetime.now()
    
    mock_operation = AsyncMock(side_effect=[
        ValueError("First attempt"),
        ValueError("Second attempt"),
        "success"
    ])
    
    result = await retry_handler.execute(mock_operation)
    
    duration = (datetime.now() - start_time).total_seconds()
    expected_min_duration = retry_handler.config.initial_delay * 3  # Sum of delays
    
    assert result == "success"
    assert duration >= expected_min_duration

@pytest.mark.asyncio
async def test_retry_metrics(retry_handler):
    """Test retry metrics collection"""
    metrics = []
    retry_handler.set_metrics_callback(metrics.append)
    
    mock_operation = AsyncMock(side_effect=[
        ValueError("First attempt"),
        "success"
    ])
    
    await retry_handler.execute(mock_operation)
    
    assert len(metrics) > 0
    assert any(m["type"] == "retry_attempt" for m in metrics)
    assert any(m["type"] == "retry_success" for m in metrics)

@pytest.mark.asyncio
async def test_retry_with_result_check(retry_handler):
    """Test retry with result validation"""
    async def check_result(result):
        return result > 0
    
    mock_operation = AsyncMock(side_effect=[0, -1, 1])
    
    result = await retry_handler.execute(
        mock_operation,
        result_validator=check_result
    )
    
    assert result == 1
    assert retry_handler.attempts == 3

@pytest.mark.asyncio
async def test_retry_with_custom_strategy(retry_handler):
    """Test retry with custom strategy"""
    # Define custom strategy
    async def custom_strategy(attempt):
        return 0.1 * attempt  # Linear increase
    
    retry_handler.add_strategy("custom", custom_strategy)
    retry_handler.config.strategy = "custom"
    
    mock_operation = AsyncMock(side_effect=[
        ValueError("First attempt"),
        "success"
    ])
    
    result = await retry_handler.execute(mock_operation)
    assert result == "success"

@pytest.mark.asyncio
async def test_retry_state_tracking(retry_handler):
    """Test retry state tracking"""
    mock_operation = AsyncMock(side_effect=[
        ValueError("First attempt"),
        ValueError("Second attempt"),
        "success"
    ])
    
    await retry_handler.execute(mock_operation)
    
    state = retry_handler.get_state()
    assert state.total_attempts == 3
    assert state.success_count == 1
    assert state.failure_count == 2

@pytest.mark.asyncio
async def test_concurrent_retries(retry_handler):
    """Test handling of concurrent retries"""
    async def flaky_operation(fail_count):
        if fail_count[0] > 0:
            fail_count[0] -= 1
            raise ValueError("Fail")
        return "success"
    
    # Run multiple operations concurrently
    operations = []
    for i in range(3):
        fail_count = [i]  # Mutable list to track fails
        operations.append(
            retry_handler.execute(lambda: flaky_operation(fail_count))
        )
    
    results = await asyncio.gather(*operations)
    assert all(r == "success" for r in results)

@pytest.mark.asyncio
async def test_retry_timeout(retry_handler):
    """Test retry timeout handling"""
    retry_handler.config.timeout = 0.5  # seconds
    
    async def slow_operation():
        await asyncio.sleep(1.0)
        return "success"
    
    with pytest.raises(RetryError) as exc_info:
        await retry_handler.execute(slow_operation)
    
    assert "Timeout" in str(exc_info.value)

@pytest.mark.asyncio
async def test_retry_cleanup(retry_handler):
    """Test retry handler cleanup"""
    mock_operation = AsyncMock(side_effect=[
        ValueError("First attempt"),
        "success"
    ])
    
    await retry_handler.execute(mock_operation)
    await retry_handler.cleanup()
    
    assert retry_handler.attempts == 0
    assert not retry_handler._is_retrying 