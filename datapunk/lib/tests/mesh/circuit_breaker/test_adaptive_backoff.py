"""Tests for the Adaptive Backoff System"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import random
from datapunk_shared.mesh.circuit_breaker.adaptive_backoff import (
    AdaptiveBackoff,
    BackoffConfig,
    BackoffStrategy,
    BackoffState
)

@pytest.fixture
def backoff_config():
    return BackoffConfig(
        initial_delay=0.1,
        max_delay=1.0,
        multiplier=2.0,
        jitter=0.1,
        pattern_window=5,
        resource_threshold=0.8
    )

@pytest.fixture
def backoff(backoff_config):
    return AdaptiveBackoff(backoff_config)

@pytest.mark.asyncio
async def test_initial_delay(backoff):
    """Test initial delay calculation"""
    delay = await backoff.get_delay("test")
    assert 0 <= delay <= backoff.config.initial_delay * (1 + backoff.config.jitter)

@pytest.mark.asyncio
async def test_exponential_backoff(backoff):
    """Test exponential backoff strategy"""
    delays = []
    for _ in range(3):
        delay = await backoff.get_delay("test")
        delays.append(delay)
        await backoff.record_attempt("test", False)
    
    # Check exponential growth pattern
    assert delays[1] > delays[0]
    assert delays[2] > delays[1]
    ratio = delays[1] / delays[0]
    assert pytest.approx(ratio, rel=0.5) == backoff.config.multiplier

@pytest.mark.asyncio
async def test_fibonacci_backoff(backoff):
    """Test Fibonacci backoff strategy"""
    # Force Fibonacci strategy
    backoff.current_strategy = BackoffStrategy.FIBONACCI
    
    delays = []
    for _ in range(4):
        delay = await backoff.get_delay("test")
        delays.append(delay)
        await backoff.record_attempt("test", False)
    
    # Check Fibonacci pattern
    assert len(delays) == 4
    assert pytest.approx(delays[3], rel=0.5) == delays[1] + delays[2]

@pytest.mark.asyncio
async def test_decorrelated_jitter(backoff):
    """Test decorrelated jitter strategy"""
    backoff.current_strategy = BackoffStrategy.DECORRELATED_JITTER
    
    delays = []
    for _ in range(5):
        delay = await backoff.get_delay("test")
        delays.append(delay)
        await backoff.record_attempt("test", False)
    
    # Check randomization
    assert len(set(delays)) > 1  # Delays should vary
    assert all(0 <= d <= backoff.config.max_delay for d in delays)

@pytest.mark.asyncio
async def test_resource_sensitive_backoff(backoff):
    """Test resource-sensitive backoff"""
    # Test with high resource usage
    delay_high = await backoff.get_delay("test", resource_usage=0.9)
    
    # Test with low resource usage
    delay_low = await backoff.get_delay("test", resource_usage=0.1)
    
    # High resource usage should lead to longer delays
    assert delay_high > delay_low

@pytest.mark.asyncio
async def test_pattern_detection(backoff):
    """Test pattern detection in failure sequences"""
    # Create repeating pattern
    pattern = [True, False, True, False]
    for success in pattern * 2:  # Repeat pattern
        await backoff.record_attempt("test", success)
    
    state = backoff._get_state("test")
    pattern_info = await backoff._detect_pattern(state)
    
    assert pattern_info is not None
    assert pattern_info["length"] == len(pattern)

@pytest.mark.asyncio
async def test_strategy_effectiveness(backoff):
    """Test strategy effectiveness calculation"""
    # Simulate successful attempts
    for _ in range(5):
        await backoff.get_delay("test")
        await backoff.record_attempt("test", True)
    
    # Check effectiveness scores
    metrics = await backoff.get_metrics()
    assert all(0 <= score <= 1 for score in 
              metrics["strategy_effectiveness"].values())

@pytest.mark.asyncio
async def test_adaptive_strategy_selection(backoff):
    """Test adaptive strategy selection"""
    # Simulate varying conditions
    scenarios = [
        (0.9, False),  # High resource usage, failure
        (0.2, True),   # Low resource usage, success
        (0.5, False),  # Medium resource usage, failure
    ]
    
    strategies = set()
    for resource_usage, success in scenarios:
        await backoff.get_delay("test", resource_usage)
        await backoff.record_attempt("test", success)
        strategies.add(backoff.current_strategy)
    
    # Should have used different strategies
    assert len(strategies) > 1

@pytest.mark.asyncio
async def test_max_delay_cap(backoff):
    """Test maximum delay cap"""
    # Force many failures to increase delay
    for _ in range(10):
        delay = await backoff.get_delay("test")
        await backoff.record_attempt("test", False)
        assert delay <= backoff.config.max_delay

@pytest.mark.asyncio
async def test_concurrent_backoff(backoff):
    """Test concurrent backoff handling"""
    async def backoff_sequence(key: str):
        for _ in range(5):
            await backoff.get_delay(key)
            await backoff.record_attempt(key, random.choice([True, False]))
            await asyncio.sleep(0.1)
    
    # Run multiple concurrent backoff sequences
    keys = ["test1", "test2", "test3"]
    await asyncio.gather(*(backoff_sequence(key) for key in keys))
    
    # Check state isolation
    metrics = await backoff.get_metrics()
    assert all(key in metrics["states"] for key in keys)
    assert len(set(state["attempts"] for state in 
                   metrics["states"].values())) == 1

@pytest.mark.asyncio
async def test_pattern_based_delay(backoff):
    """Test pattern-based delay calculation"""
    # Create a clear pattern
    pattern = [True, False] * 3
    for success in pattern:
        await backoff.get_delay("test")
        await backoff.record_attempt("test", success)
    
    # Force pattern-based strategy
    backoff.current_strategy = BackoffStrategy.PATTERN_BASED
    delay = await backoff.get_delay("test")
    
    # Delay should be based on pattern interval
    assert delay > 0
    assert delay <= backoff.config.max_delay

@pytest.mark.asyncio
async def test_metrics_collection(backoff):
    """Test metrics collection and reporting"""
    # Generate some backoff activity
    for _ in range(5):
        await backoff.get_delay("test")
        await backoff.record_attempt("test", random.choice([True, False]))
    
    metrics = await backoff.get_metrics()
    
    # Check metrics structure
    assert "strategy_effectiveness" in metrics
    assert "current_strategy" in metrics
    assert "pattern_history" in metrics
    assert "states" in metrics
    assert "test" in metrics["states"]

@pytest.mark.asyncio
async def test_error_handling(backoff):
    """Test error handling in backoff system"""
    with patch.object(backoff, '_calculate_delay', 
                     side_effect=Exception("Test error")):
        # Should handle error and return initial delay
        delay = await backoff.get_delay("test")
        assert delay == backoff.config.initial_delay

@pytest.mark.asyncio
async def test_state_cleanup(backoff):
    """Test state cleanup for old entries"""
    # Create some old state entries
    old_time = datetime.utcnow() - timedelta(hours=1)
    state = backoff._get_state("old_test")
    state.last_attempt = old_time
    
    # Add some recent entries
    await backoff.get_delay("new_test")
    
    # Check state management
    assert "old_test" in backoff.states
    assert "new_test" in backoff.states

@pytest.mark.asyncio
async def test_adaptive_strategy_weights(backoff):
    """Test adaptive strategy weight calculations"""
    backoff.current_strategy = BackoffStrategy.ADAPTIVE
    
    # Record mixed success/failure pattern
    for success in [True, False, True, True, False]:
        await backoff.get_delay("test")
        await backoff.record_attempt("test", success)
    
    # Get delay using adaptive strategy
    delay = await backoff.get_delay("test")
    
    # Should be within bounds
    assert backoff.config.initial_delay <= delay <= backoff.config.max_delay 