"""
Circuit Breaker Test Suite

Tests the circuit breaker implementation including:
- Basic circuit breaker functionality
- Advanced circuit breaker features
- Gradual recovery strategy
- Distributed state management
- Metric collection

Run with: pytest -v test_circuit_breaker.py
"""

import pytest
from datetime import datetime, timedelta
import asyncio
from unittest.mock import Mock, AsyncMock

from datapunk_shared.mesh.circuit_breaker.circuit_breaker_strategies import (
    CircuitState,
    CircuitBreakerStrategy,
    GradualRecoveryStrategy
)
from datapunk_shared.mesh.circuit_breaker.circuit_breaker_advanced import (
    AdvancedCircuitBreaker
)

# Fixtures

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.record_gauge = AsyncMock()
    client.increment = AsyncMock()
    return client

@pytest.fixture
def cache_client():
    """Mock cache client for testing."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    return client

@pytest.fixture
async def gradual_strategy(metrics_client):
    """Create gradual recovery strategy for testing."""
    return GradualRecoveryStrategy(
        metrics=metrics_client,
        base_recovery_rate=0.1,
        recovery_step=0.2,  # Faster recovery for testing
        error_threshold=0.1
    )

@pytest.fixture
async def circuit_breaker(metrics_client, cache_client, gradual_strategy):
    """Create circuit breaker instance for testing."""
    return AdvancedCircuitBreaker(
        service_name="test_service",
        metrics=metrics_client,
        cache=cache_client,
        strategy=gradual_strategy
    )

# Strategy Tests

@pytest.mark.asyncio
async def test_gradual_strategy_initial_state(gradual_strategy):
    """Test initial state of gradual recovery strategy."""
    assert gradual_strategy.base_recovery_rate == 0.1
    assert gradual_strategy.recovery_step == 0.2
    assert gradual_strategy.error_threshold == 0.1
    assert gradual_strategy.current_recovery_rate == 0.1
    assert gradual_strategy._recovery_start_time is None

@pytest.mark.asyncio
async def test_gradual_strategy_should_open(gradual_strategy):
    """Test failure detection logic."""
    # Should open on high error rate
    assert await gradual_strategy.should_open(5, 0.3) is True
    
    # Should not open on acceptable error rate
    assert await gradual_strategy.should_open(2, 0.05) is False
    
    # More sensitive during recovery
    gradual_strategy._recovery_start_time = datetime.utcnow()
    assert await gradual_strategy.should_open(1, 0.15) is True

@pytest.mark.asyncio
async def test_gradual_strategy_recovery_progression(gradual_strategy):
    """Test gradual traffic increase during recovery."""
    # Initial state
    rate = await gradual_strategy.get_allowed_request_rate()
    assert rate == 1.0  # Full traffic when not in recovery
    
    # Start recovery
    assert await gradual_strategy.should_close(0) is False
    assert await gradual_strategy.should_close(3) is False
    
    # Check progression
    current_rate = gradual_strategy.current_recovery_rate
    assert 0.3 <= current_rate <= 0.4  # Initial + 1 step
    
    # Multiple success windows
    for _ in range(3):
        await gradual_strategy.should_close(3)
    
    # Should be at higher traffic level
    assert gradual_strategy.current_recovery_rate > 0.6

@pytest.mark.asyncio
async def test_gradual_strategy_reset(gradual_strategy):
    """Test strategy reset on failures."""
    # Progress recovery
    await gradual_strategy.should_close(3)
    assert gradual_strategy.current_recovery_rate > 0.1
    
    # Reset
    await gradual_strategy.reset_recovery()
    assert gradual_strategy.current_recovery_rate == 0.1
    assert gradual_strategy._recovery_start_time is None

# Circuit Breaker Tests

@pytest.mark.asyncio
async def test_circuit_breaker_initial_state(circuit_breaker):
    """Test initial circuit breaker state."""
    assert await circuit_breaker.allow_request() is True
    assert circuit_breaker.state == CircuitState.CLOSED

@pytest.mark.asyncio
async def test_circuit_breaker_open_on_failures(circuit_breaker):
    """Test circuit opens after failures."""
    # Record failures
    for _ in range(5):
        await circuit_breaker.record_failure()
    
    # Should be open
    assert not await circuit_breaker.allow_request()
    assert circuit_breaker.state == CircuitState.OPEN

@pytest.mark.asyncio
async def test_circuit_breaker_gradual_recovery(circuit_breaker):
    """Test gradual recovery process."""
    # Open circuit
    for _ in range(5):
        await circuit_breaker.record_failure()
    
    # Force recovery timeout
    circuit_breaker._last_failure_time = datetime.utcnow() - timedelta(seconds=31)
    
    # Track allowed requests during recovery
    allowed_count = 0
    total_requests = 100
    
    for _ in range(total_requests):
        if await circuit_breaker.allow_request():
            allowed_count += 1
            await circuit_breaker.record_success()
    
    # Should have allowed roughly 10-30% of requests initially
    assert 10 <= (allowed_count / total_requests) * 100 <= 30

@pytest.mark.asyncio
async def test_circuit_breaker_distributed_state(circuit_breaker, cache_client):
    """Test distributed state management."""
    # Set up cache mock
    cache_client.get.return_value = CircuitState.OPEN.value
    
    # Should respect cached state
    assert not await circuit_breaker.allow_request()
    
    # Should update cache on state change
    await circuit_breaker._transition_state(CircuitState.CLOSED)
    cache_client.set.assert_called_once()

@pytest.mark.asyncio
async def test_circuit_breaker_metrics(circuit_breaker, metrics_client):
    """Test metric collection."""
    # Record failure
    await circuit_breaker.record_failure()
    
    # Should record metrics
    metrics_client.increment.assert_called()
    
    # Record recovery
    await circuit_breaker.record_success()
    assert metrics_client.record_gauge.call_count > 0

# Error Handling Tests

@pytest.mark.asyncio
async def test_circuit_breaker_cache_failure(circuit_breaker, cache_client):
    """Test graceful handling of cache failures."""
    # Simulate cache failure
    cache_client.get.side_effect = Exception("Cache error")
    
    # Should fall back to local state
    assert await circuit_breaker.allow_request() is True

@pytest.mark.asyncio
async def test_circuit_breaker_metric_failure(circuit_breaker, metrics_client):
    """Test graceful handling of metric failures."""
    # Simulate metrics failure
    metrics_client.increment.side_effect = Exception("Metrics error")
    
    # Should continue operating
    await circuit_breaker.record_failure()
    assert circuit_breaker.failure_count == 1 