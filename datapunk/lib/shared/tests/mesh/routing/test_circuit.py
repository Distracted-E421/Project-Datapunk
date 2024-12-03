import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.routing import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerError,
    FailureStrategy
)

@pytest.fixture
def circuit_config():
    return CircuitBreakerConfig(
        failure_threshold=3,
        reset_timeout=5,
        half_open_timeout=2,
        success_threshold=2,
        failure_strategy=FailureStrategy.CONSECUTIVE
    )

@pytest.fixture
def circuit_breaker(circuit_config):
    return CircuitBreaker(config=circuit_config)

@pytest.mark.asyncio
async def test_circuit_initialization(circuit_breaker, circuit_config):
    assert circuit_breaker.config == circuit_config
    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.failure_count == 0

@pytest.mark.asyncio
async def test_circuit_trip():
    breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=2))
    
    # Record failures to trip circuit
    await breaker.record_failure()
    assert breaker.state == CircuitState.CLOSED
    
    await breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    assert breaker.last_failure_time is not None

@pytest.mark.asyncio
async def test_circuit_reset():
    breaker = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=1,
        reset_timeout=0.1
    ))
    
    # Trip circuit
    await breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    
    # Wait for reset timeout
    await asyncio.sleep(0.2)
    
    # Circuit should transition to half-open
    assert breaker.state == CircuitState.HALF_OPEN

@pytest.mark.asyncio
async def test_half_open_success():
    breaker = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=1,
        success_threshold=2
    ))
    
    # Trip and reset circuit
    await breaker.record_failure()
    await breaker.attempt_reset()
    
    # Record successes in half-open state
    await breaker.record_success()
    assert breaker.state == CircuitState.HALF_OPEN
    
    await breaker.record_success()
    assert breaker.state == CircuitState.CLOSED

@pytest.mark.asyncio
async def test_half_open_failure():
    breaker = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=1,
        success_threshold=2
    ))
    
    # Trip and reset circuit
    await breaker.record_failure()
    await breaker.attempt_reset()
    
    # Failure in half-open should reopen circuit
    await breaker.record_failure()
    assert breaker.state == CircuitState.OPEN

@pytest.mark.asyncio
async def test_consecutive_failures():
    breaker = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=3,
        failure_strategy=FailureStrategy.CONSECUTIVE
    ))
    
    # Record failures with success in between
    await breaker.record_failure()
    await breaker.record_failure()
    await breaker.record_success()  # Resets consecutive count
    await breaker.record_failure()
    
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 1

@pytest.mark.asyncio
async def test_percentage_failures():
    breaker = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=0.5,  # 50% failure rate
        failure_strategy=FailureStrategy.PERCENTAGE,
        window_size=4
    ))
    
    # Record 2 failures and 2 successes
    await breaker.record_failure()
    await breaker.record_success()
    await breaker.record_failure()
    await breaker.record_success()
    
    assert breaker.state == CircuitState.CLOSED
    
    # One more failure should trip (3/5 = 60% failure rate)
    await breaker.record_failure()
    assert breaker.state == CircuitState.OPEN

@pytest.mark.asyncio
async def test_circuit_metrics(circuit_breaker):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        await circuit_breaker.record_failure()
        await circuit_breaker.record_success()
        
        mock_collector.return_value.record_gauge.assert_called()
        mock_collector.return_value.record_counter.assert_called()

@pytest.mark.asyncio
async def test_circuit_events(circuit_breaker):
    events = []
    
    def event_handler(event_type, circuit_id):
        events.append((event_type, circuit_id))
    
    circuit_breaker.on_state_change(event_handler)
    
    # Trip circuit
    for _ in range(circuit_breaker.config.failure_threshold):
        await circuit_breaker.record_failure()
    
    assert len(events) > 0
    assert events[-1][0] == "opened"

@pytest.mark.asyncio
async def test_concurrent_access(circuit_breaker):
    # Test concurrent failure recording
    await asyncio.gather(*[
        circuit_breaker.record_failure()
        for _ in range(5)
    ])
    
    assert circuit_breaker.failure_count <= circuit_breaker.config.failure_threshold
    assert circuit_breaker.state in [CircuitState.CLOSED, CircuitState.OPEN]

@pytest.mark.asyncio
async def test_custom_failure_detector():
    async def custom_detector(error):
        return isinstance(error, ValueError)
    
    breaker = CircuitBreaker(
        CircuitBreakerConfig(failure_threshold=1),
        failure_detector=custom_detector
    )
    
    # Should not count as failure
    await breaker.handle_error(TypeError())
    assert breaker.state == CircuitState.CLOSED
    
    # Should count as failure
    await breaker.handle_error(ValueError())
    assert breaker.state == CircuitState.OPEN

@pytest.mark.asyncio
async def test_circuit_timeout():
    breaker = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=1,
        timeout_seconds=0.1
    ))
    
    async def slow_operation():
        await asyncio.sleep(0.2)
        return True
    
    # Should timeout and count as failure
    with pytest.raises(CircuitBreakerError):
        await breaker.execute(slow_operation)
    
    assert breaker.state == CircuitState.OPEN

@pytest.mark.asyncio
async def test_circuit_fallback():
    breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=1))
    
    async def operation():
        raise ValueError("Failed")
    
    async def fallback():
        return "fallback"
    
    # First call should use fallback
    result = await breaker.execute(operation, fallback=fallback)
    assert result == "fallback"
    
    # Circuit should be open
    assert breaker.state == CircuitState.OPEN

@pytest.mark.asyncio
async def test_state_persistence(circuit_breaker):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        await circuit_breaker.save_state()
        mock_file.write.assert_called_once()
        
        await circuit_breaker.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(circuit_breaker):
    with pytest.raises(CircuitBreakerError):
        await circuit_breaker.execute(lambda: 1/0)

@pytest.mark.asyncio
async def test_circuit_reset_schedule():
    breaker = CircuitBreaker(CircuitBreakerConfig(
        failure_threshold=1,
        reset_timeout=0.1,
        reset_schedule=[0.1, 0.2, 0.3]  # Progressive backoff
    ))
    
    await breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    
    # First reset attempt
    await asyncio.sleep(0.15)
    assert breaker.state == CircuitState.HALF_OPEN
    
    # Fail again
    await breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    
    # Second reset attempt should take longer
    await asyncio.sleep(0.15)
    assert breaker.state == CircuitState.OPEN 