"""Tests for the Rate Limiting Strategy"""

import pytest
import asyncio
import time
from unittest.mock import patch
from datetime import datetime, timedelta

from datapunk_shared.mesh.circuit_breaker.rate_limiting_strategy import (
    RateLimitingStrategy,
    RateLimitConfig,
    RateLimitAlgorithm,
    TokenBucket,
    LeakyBucket,
    FixedWindow,
    SlidingWindow
)

@pytest.fixture
def config():
    return RateLimitConfig(
        algorithm=RateLimitAlgorithm.ADAPTIVE,
        requests_per_second=100.0,
        burst_size=50,
        window_size_seconds=1.0,
        min_rate=10.0,
        max_rate=1000.0,
        scale_factor=1.5,
        cooldown_seconds=0.1  # Short cooldown for testing
    )

@pytest.fixture
def strategy(config):
    return RateLimitingStrategy(config)

@pytest.mark.asyncio
async def test_token_bucket():
    """Test token bucket algorithm"""
    bucket = TokenBucket(rate=10.0, capacity=5)
    
    # Should allow burst up to capacity
    assert all([await bucket.acquire() for _ in range(5)])
    
    # Should reject when empty
    assert not await bucket.acquire()
    
    # Should refill over time
    await asyncio.sleep(0.2)  # Should add 2 tokens
    assert await bucket.acquire()
    assert await bucket.acquire()
    assert not await bucket.acquire()

@pytest.mark.asyncio
async def test_leaky_bucket():
    """Test leaky bucket algorithm"""
    bucket = LeakyBucket(rate=10.0, capacity=5)
    
    # Should allow burst up to capacity
    assert all([await bucket.acquire() for _ in range(5)])
    
    # Should reject when full
    assert not await bucket.acquire()
    
    # Should leak over time
    await asyncio.sleep(0.2)  # Should leak 2 requests
    assert await bucket.acquire()
    assert await bucket.acquire()
    assert not await bucket.acquire()

@pytest.mark.asyncio
async def test_fixed_window():
    """Test fixed window algorithm"""
    window = FixedWindow(limit=5, window_seconds=1.0)
    
    # Should allow up to limit
    assert all([await window.acquire() for _ in range(5)])
    
    # Should reject when limit reached
    assert not await window.acquire()
    
    # Should reset after window
    await asyncio.sleep(1.1)
    assert await window.acquire()

@pytest.mark.asyncio
async def test_sliding_window():
    """Test sliding window algorithm"""
    window = SlidingWindow(limit=5, window_seconds=1.0)
    
    # Should allow up to limit
    assert all([await window.acquire() for _ in range(5)])
    
    # Should reject when limit reached
    assert not await window.acquire()
    
    # Should allow after old requests expire
    await asyncio.sleep(1.1)
    assert await window.acquire()

@pytest.mark.asyncio
async def test_adaptive_strategy(strategy):
    """Test adaptive strategy behavior"""
    # Should allow initial requests
    assert await strategy.should_allow_request()
    
    # Record mixed success/failure
    for _ in range(10):
        await strategy.record_success()
    for _ in range(2):
        await strategy.record_failure()
        
    # Wait for rate adjustment
    await asyncio.sleep(strategy.config.cooldown_seconds)
    
    # Should adjust rate based on error rate
    metrics = await strategy.get_metrics()
    assert metrics["error_rate"] > 0
    assert metrics["current_rate"] < strategy.config.requests_per_second

@pytest.mark.asyncio
async def test_rate_adjustment(strategy):
    """Test rate adjustment based on error rates"""
    # Record high error rate
    for _ in range(8):
        await strategy.record_failure()
    for _ in range(2):
        await strategy.record_success()
        
    await asyncio.sleep(strategy.config.cooldown_seconds)
    
    # Rate should decrease
    assert strategy.current_rate < strategy.config.requests_per_second
    
    # Record low error rate
    for _ in range(98):
        await strategy.record_success()
    for _ in range(2):
        await strategy.record_failure()
        
    await asyncio.sleep(strategy.config.cooldown_seconds)
    
    # Rate should increase
    assert strategy.current_rate > strategy.config.requests_per_second

@pytest.mark.asyncio
async def test_algorithm_switching(config):
    """Test different rate limiting algorithms"""
    for algorithm in RateLimitAlgorithm:
        config.algorithm = algorithm
        strategy = RateLimitingStrategy(config)
        
        # Test basic functionality
        assert await strategy.should_allow_request()
        
        # Test rate limiting
        requests = [strategy.should_allow_request() for _ in range(100)]
        results = await asyncio.gather(*requests)
        
        # Some requests should be rejected
        assert not all(results)

@pytest.mark.asyncio
async def test_concurrent_requests(strategy):
    """Test concurrent request handling"""
    async def make_request():
        if await strategy.should_allow_request():
            await strategy.record_success()
            return True
        await strategy.record_failure()
        return False
    
    # Make concurrent requests
    tasks = [make_request() for _ in range(100)]
    results = await asyncio.gather(*tasks)
    
    # Some requests should succeed, some should fail
    assert any(results)
    assert not all(results)

@pytest.mark.asyncio
async def test_metrics_collection(strategy):
    """Test metrics collection"""
    # Generate some activity
    for _ in range(5):
        assert await strategy.should_allow_request()
        await strategy.record_success()
    
    for _ in range(2):
        await strategy.record_failure()
    
    metrics = await strategy.get_metrics()
    
    assert metrics["success_count"] == 5
    assert metrics["failure_count"] == 2
    assert 0.2 < metrics["error_rate"] < 0.3
    assert "current_rate" in metrics
    assert "algorithm" in metrics
    assert "last_adjustment" in metrics

@pytest.mark.asyncio
async def test_rate_limits(strategy):
    """Test rate limit boundaries"""
    # Test minimum rate
    for _ in range(100):
        await strategy.record_failure()
        
    await asyncio.sleep(strategy.config.cooldown_seconds)
    assert strategy.current_rate >= strategy.config.min_rate
    
    # Test maximum rate
    for _ in range(100):
        await strategy.record_success()
        
    await asyncio.sleep(strategy.config.cooldown_seconds)
    assert strategy.current_rate <= strategy.config.max_rate

@pytest.mark.asyncio
async def test_burst_handling(strategy):
    """Test burst request handling"""
    # Should handle burst up to burst_size
    burst_results = [
        await strategy.should_allow_request()
        for _ in range(strategy.config.burst_size)
    ]
    assert all(burst_results)
    
    # Should reject excess burst
    assert not await strategy.should_allow_request()
    
    # Should recover after cooldown
    await asyncio.sleep(1.0)
    assert await strategy.should_allow_request()

@pytest.mark.asyncio
async def test_error_handling(strategy):
    """Test error handling and recovery"""
    # Simulate error burst
    for _ in range(10):
        await strategy.record_failure()
        
    await asyncio.sleep(strategy.config.cooldown_seconds)
    initial_rate = strategy.current_rate
    
    # Simulate recovery
    for _ in range(10):
        await strategy.record_success()
        
    await asyncio.sleep(strategy.config.cooldown_seconds)
    recovery_rate = strategy.current_rate
    
    assert recovery_rate > initial_rate 