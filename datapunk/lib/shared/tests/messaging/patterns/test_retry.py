import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.messaging.patterns.retry import RetryPattern, RetryConfig
from datapunk_shared.monitoring import MetricsClient
from datapunk_shared.tracing import TracingManager

@pytest.fixture
def retry_config():
    return RetryConfig(
        max_retries=3,
        initial_delay=1,
        max_delay=30,
        backoff_factor=2,
        jitter=0.1
    )

@pytest.fixture
def mock_metrics():
    return MagicMock(spec=MetricsClient)

@pytest.fixture
def mock_tracing():
    return MagicMock(spec=TracingManager)

@pytest.fixture
def retry_pattern(retry_config, mock_metrics, mock_tracing):
    return RetryPattern(retry_config, mock_metrics, mock_tracing)

@pytest.mark.asyncio
async def test_retry_calculation(retry_pattern):
    """Test retry delay calculation with backoff"""
    # First retry
    delay = retry_pattern.calculate_delay(1)
    assert 0.9 <= delay <= 1.1  # Account for jitter
    
    # Second retry
    delay = retry_pattern.calculate_delay(2)
    assert 1.8 <= delay <= 2.2  # Account for jitter
    
    # Third retry
    delay = retry_pattern.calculate_delay(3)
    assert 3.6 <= delay <= 4.4  # Account for jitter

@pytest.mark.asyncio
async def test_max_delay_cap(retry_pattern):
    """Test that delay is capped at max_delay"""
    delay = retry_pattern.calculate_delay(10)  # High retry count
    assert delay <= retry_pattern.config.max_delay

@pytest.mark.asyncio
async def test_retry_execution(retry_pattern):
    """Test retry execution with success"""
    operation = AsyncMock()
    operation.side_effect = [Exception("First try"), Exception("Second try"), "Success"]
    
    result = await retry_pattern.execute(operation)
    assert result == "Success"
    assert operation.call_count == 3
    
    # Verify metrics
    retry_pattern.metrics.increment.assert_any_call(
        'retry_attempts_total',
        {'attempt': '1'}
    )
    retry_pattern.metrics.increment.assert_any_call(
        'retry_attempts_total',
        {'attempt': '2'}
    )
    retry_pattern.metrics.increment.assert_any_call(
        'retry_success_total'
    )

@pytest.mark.asyncio
async def test_retry_exhaustion(retry_pattern):
    """Test retry exhaustion after max attempts"""
    operation = AsyncMock(side_effect=Exception("Always fails"))
    
    with pytest.raises(Exception):
        await retry_pattern.execute(operation)
    
    assert operation.call_count == retry_pattern.config.max_retries + 1
    retry_pattern.metrics.increment.assert_any_call('retry_exhaustion_total')

@pytest.mark.asyncio
async def test_retry_immediate_success(retry_pattern):
    """Test immediate success without retries"""
    operation = AsyncMock(return_value="Success")
    
    result = await retry_pattern.execute(operation)
    assert result == "Success"
    assert operation.call_count == 1
    
    # Verify no retry metrics
    retry_pattern.metrics.increment.assert_not_called()

@pytest.mark.asyncio
async def test_retry_with_context(retry_pattern):
    """Test retry with context propagation"""
    context = {"request_id": "test-123"}
    operation = AsyncMock(side_effect=[Exception("First try"), "Success"])
    
    result = await retry_pattern.execute(operation, context=context)
    assert result == "Success"
    
    # Verify context was passed to operation
    operation.assert_any_call(context=context)

@pytest.mark.asyncio
async def test_retry_with_custom_predicate(retry_pattern):
    """Test retry with custom retry predicate"""
    def retry_on_value_error(exc):
        return isinstance(exc, ValueError)
    
    operation = AsyncMock(side_effect=[ValueError("Retry me"), TypeError("Don't retry")])
    
    with pytest.raises(TypeError):
        await retry_pattern.execute(operation, retry_predicate=retry_on_value_error)
    
    assert operation.call_count == 2

@pytest.mark.asyncio
async def test_retry_metrics_and_tracing(retry_pattern):
    """Test metrics and tracing integration"""
    operation = AsyncMock(side_effect=[Exception("First try"), "Success"])
    
    await retry_pattern.execute(operation)
    
    # Verify metrics
    retry_pattern.metrics.increment.assert_any_call(
        'retry_attempts_total',
        {'attempt': '1'}
    )
    retry_pattern.metrics.increment.assert_any_call(
        'retry_success_total'
    )
    
    # Verify tracing
    retry_pattern.tracing.set_attribute.assert_any_call(
        'retry.attempt', 1
    )
    retry_pattern.tracing.set_attribute.assert_any_call(
        'retry.success', True
    )

@pytest.mark.asyncio
async def test_retry_with_timeout(retry_pattern):
    """Test retry with operation timeout"""
    async def slow_operation():
        await asyncio.sleep(2)
        return "Success"
    
    operation = AsyncMock(wraps=slow_operation)
    
    with pytest.raises(asyncio.TimeoutError):
        await retry_pattern.execute(operation, timeout=1)
    
    retry_pattern.metrics.increment.assert_any_call('retry_timeout_total') 