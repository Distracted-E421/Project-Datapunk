import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.security.rate_limit import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStrategy,
    RateLimitResult,
    RateLimitError
)

@pytest.fixture
def rate_limit_config():
    return RateLimitConfig(
        name="test_limiter",
        strategies=[
            {
                "name": "api_default",
                "type": RateLimitStrategy.TOKEN_BUCKET,
                "rate": 100,  # requests per second
                "burst": 20,
                "window": 1  # second
            },
            {
                "name": "auth_endpoints",
                "type": RateLimitStrategy.FIXED_WINDOW,
                "rate": 10,  # requests per minute
                "window": 60  # seconds
            }
        ],
        storage_type="redis",
        storage_config={
            "host": "localhost",
            "port": 6379,
            "db": 0
        },
        metrics_enabled=True,
        notification_enabled=True
    )

@pytest.fixture
def mock_storage():
    return AsyncMock()

@pytest.fixture
async def rate_limiter(rate_limit_config, mock_storage):
    limiter = RateLimiter(rate_limit_config)
    limiter.storage = mock_storage
    await limiter.initialize()
    return limiter

@pytest.mark.asyncio
async def test_limiter_initialization(rate_limiter, rate_limit_config):
    """Test rate limiter initialization"""
    assert rate_limiter.config == rate_limit_config
    assert rate_limiter.is_initialized
    assert len(rate_limiter.strategies) == len(rate_limit_config.strategies)

@pytest.mark.asyncio
async def test_token_bucket_strategy(rate_limiter):
    """Test token bucket rate limiting strategy"""
    client_id = "test_client"
    strategy = "api_default"
    
    # First request should pass
    result = await rate_limiter.check_rate_limit(client_id, strategy)
    assert result.is_allowed
    assert result.remaining_tokens > 0
    
    # Simulate burst
    results = []
    for _ in range(25):  # More than burst size
        results.append(await rate_limiter.check_rate_limit(client_id, strategy))
    
    assert sum(1 for r in results if r.is_allowed) == 20  # Burst size
    assert sum(1 for r in results if not r.is_allowed) == 5  # Excess requests

@pytest.mark.asyncio
async def test_fixed_window_strategy(rate_limiter):
    """Test fixed window rate limiting strategy"""
    client_id = "test_client"
    strategy = "auth_endpoints"
    
    # First set of requests within window
    results = []
    for _ in range(12):  # More than window limit
        results.append(await rate_limiter.check_rate_limit(client_id, strategy))
    
    assert sum(1 for r in results if r.is_allowed) == 10  # Window limit
    assert sum(1 for r in results if not r.is_allowed) == 2  # Excess requests
    
    # Wait for window reset
    await asyncio.sleep(60)
    
    # Should be allowed again
    result = await rate_limiter.check_rate_limit(client_id, strategy)
    assert result.is_allowed

@pytest.mark.asyncio
async def test_sliding_window_strategy(rate_limiter):
    """Test sliding window rate limiting"""
    # Add sliding window strategy
    await rate_limiter.add_strategy({
        "name": "sliding_window",
        "type": RateLimitStrategy.SLIDING_WINDOW,
        "rate": 50,
        "window": 30  # seconds
    })
    
    client_id = "test_client"
    strategy = "sliding_window"
    
    # Test requests across window boundaries
    results = []
    for i in range(60):
        if i % 10 == 0:
            await asyncio.sleep(0.1)  # Simulate time passing
        results.append(await rate_limiter.check_rate_limit(client_id, strategy))
    
    assert sum(1 for r in results if r.is_allowed) == 50  # Window limit

@pytest.mark.asyncio
async def test_rate_limit_metrics(rate_limiter):
    """Test rate limit metrics collection"""
    metrics = []
    rate_limiter.set_metrics_callback(metrics.append)
    
    client_id = "test_client"
    strategy = "api_default"
    
    # Generate some traffic
    for _ in range(10):
        await rate_limiter.check_rate_limit(client_id, strategy)
    
    assert len(metrics) > 0
    assert any(m["type"] == "rate_limit_check" for m in metrics)
    assert any(m["type"] == "rate_limit_exceeded" for m in metrics)

@pytest.mark.asyncio
async def test_rate_limit_notifications(rate_limiter):
    """Test rate limit notifications"""
    notification_handler = AsyncMock()
    rate_limiter.set_notification_handler(notification_handler)
    
    client_id = "test_client"
    strategy = "api_default"
    
    # Generate excess traffic
    for _ in range(25):  # More than burst size
        await rate_limiter.check_rate_limit(client_id, strategy)
    
    notification_handler.assert_called()

@pytest.mark.asyncio
async def test_dynamic_rate_adjustment(rate_limiter):
    """Test dynamic rate limit adjustment"""
    client_id = "test_client"
    strategy = "api_default"
    
    # Adjust rate limit
    await rate_limiter.adjust_rate_limit(
        strategy,
        new_rate=200,
        new_burst=40
    )
    
    # Test with new limits
    results = []
    for _ in range(45):  # More than new burst size
        results.append(await rate_limiter.check_rate_limit(client_id, strategy))
    
    assert sum(1 for r in results if r.is_allowed) == 40  # New burst size

@pytest.mark.asyncio
async def test_client_specific_limits(rate_limiter):
    """Test client-specific rate limits"""
    client_id = "premium_client"
    strategy = "api_default"
    
    # Set client-specific limit
    await rate_limiter.set_client_limit(
        client_id,
        strategy,
        rate=200,
        burst=50
    )
    
    # Test with client-specific limits
    results = []
    for _ in range(55):  # More than client burst size
        results.append(await rate_limiter.check_rate_limit(client_id, strategy))
    
    assert sum(1 for r in results if r.is_allowed) == 50  # Client burst size

@pytest.mark.asyncio
async def test_error_handling(rate_limiter):
    """Test error handling"""
    # Test with invalid strategy
    with pytest.raises(RateLimitError):
        await rate_limiter.check_rate_limit("test_client", "invalid_strategy")
    
    # Test with invalid client ID
    with pytest.raises(RateLimitError):
        await rate_limiter.check_rate_limit(None, "api_default")

@pytest.mark.asyncio
async def test_rate_limit_cleanup(rate_limiter):
    """Test rate limit data cleanup"""
    # Generate some rate limit data
    client_id = "test_client"
    strategy = "api_default"
    
    for _ in range(10):
        await rate_limiter.check_rate_limit(client_id, strategy)
    
    # Clean up expired data
    cleanup_result = await rate_limiter.cleanup_expired_data()
    assert cleanup_result.success
    assert cleanup_result.cleaned_keys >= 0

@pytest.mark.asyncio
async def test_concurrent_requests(rate_limiter):
    """Test handling of concurrent rate limit requests"""
    client_id = "test_client"
    strategy = "api_default"
    
    # Simulate concurrent requests
    async def make_request():
        return await rate_limiter.check_rate_limit(client_id, strategy)
    
    tasks = [make_request() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    # Verify consistent state
    assert len(results) == 10
    assert all(isinstance(r, RateLimitResult) for r in results)

@pytest.mark.asyncio
async def test_rate_limit_persistence(rate_limiter):
    """Test rate limit state persistence"""
    client_id = "test_client"
    strategy = "api_default"
    
    # Generate some state
    for _ in range(5):
        await rate_limiter.check_rate_limit(client_id, strategy)
    
    # Save state
    save_result = await rate_limiter.save_state()
    assert save_result.success
    
    # Load state
    load_result = await rate_limiter.load_state()
    assert load_result.success
    assert load_result.loaded_keys > 0 