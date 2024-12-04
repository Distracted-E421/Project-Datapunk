import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.auth import (
    RateLimiter,
    RateLimitConfig,
    RateLimit,
    RateLimitExceeded,
    RateLimitMetrics
)

@pytest.fixture
def rate_config():
    return RateLimitConfig(
        default_rate=100,  # requests per minute
        burst_multiplier=2,
        window_size=60,  # seconds
        cleanup_interval=300  # 5 minutes
    )

@pytest.fixture
def rate_limiter(rate_config):
    return RateLimiter(config=rate_config)

@pytest.fixture
def sample_limits():
    return [
        RateLimit(
            client_id="client1",
            rate=50,
            window_size=60,
            burst_allowed=True
        ),
        RateLimit(
            client_id="client2",
            rate=200,
            window_size=60,
            burst_allowed=False
        )
    ]

@pytest.mark.asyncio
async def test_limiter_initialization(rate_limiter, rate_config):
    assert rate_limiter.config == rate_config
    assert rate_limiter.is_initialized
    assert len(rate_limiter.client_limits) == 0

@pytest.mark.asyncio
async def test_rate_limit_registration(rate_limiter, sample_limits):
    for limit in sample_limits:
        await rate_limiter.register_limit(limit)
    
    assert len(rate_limiter.client_limits) == len(sample_limits)
    assert all(l.client_id in rate_limiter.client_limits 
              for l in sample_limits)

@pytest.mark.asyncio
async def test_request_tracking(rate_limiter):
    client_id = "test_client"
    
    # Track multiple requests
    for _ in range(5):
        await rate_limiter.track_request(client_id)
    
    stats = await rate_limiter.get_client_stats(client_id)
    assert stats.request_count == 5

@pytest.mark.asyncio
async def test_rate_limit_enforcement(rate_limiter, sample_limits):
    # Register a limit
    limit = sample_limits[0]  # 50 requests per minute
    await rate_limiter.register_limit(limit)
    
    # Make requests up to limit
    for _ in range(50):
        await rate_limiter.check_rate_limit(limit.client_id)
    
    # Next request should fail
    with pytest.raises(RateLimitExceeded):
        await rate_limiter.check_rate_limit(limit.client_id)

@pytest.mark.asyncio
async def test_burst_allowance(rate_limiter):
    # Register a limit with burst allowed
    limit = RateLimit(
        client_id="burst_client",
        rate=10,
        window_size=60,
        burst_allowed=True
    )
    await rate_limiter.register_limit(limit)
    
    # Make requests up to normal limit
    for _ in range(10):
        await rate_limiter.check_rate_limit(limit.client_id)
    
    # Should allow burst requests
    for _ in range(10):  # Additional burst capacity
        await rate_limiter.check_rate_limit(limit.client_id)
    
    # Should fail after burst capacity is exhausted
    with pytest.raises(RateLimitExceeded):
        await rate_limiter.check_rate_limit(limit.client_id)

@pytest.mark.asyncio
async def test_window_sliding(rate_limiter):
    client_id = "window_test"
    limit = RateLimit(
        client_id=client_id,
        rate=10,
        window_size=1,  # 1 second window
        burst_allowed=False
    )
    await rate_limiter.register_limit(limit)
    
    # Make requests
    for _ in range(10):
        await rate_limiter.check_rate_limit(client_id)
    
    # Wait for window to slide
    await asyncio.sleep(1.1)
    
    # Should allow new requests
    await rate_limiter.check_rate_limit(client_id)

@pytest.mark.asyncio
async def test_dynamic_rate_adjustment(rate_limiter):
    client_id = "dynamic_client"
    initial_limit = RateLimit(
        client_id=client_id,
        rate=100,
        window_size=60,
        burst_allowed=True
    )
    await rate_limiter.register_limit(initial_limit)
    
    # Adjust rate limit
    new_rate = 150
    await rate_limiter.update_rate_limit(
        client_id=client_id,
        new_rate=new_rate
    )
    
    limit = rate_limiter.client_limits[client_id]
    assert limit.rate == new_rate

@pytest.mark.asyncio
async def test_concurrent_requests(rate_limiter):
    client_id = "concurrent_client"
    limit = RateLimit(
        client_id=client_id,
        rate=100,
        window_size=60,
        burst_allowed=False
    )
    await rate_limiter.register_limit(limit)
    
    # Make concurrent requests
    tasks = [
        rate_limiter.check_rate_limit(client_id)
        for _ in range(100)
    ]
    
    # All should succeed
    await asyncio.gather(*tasks)
    
    # Next request should fail
    with pytest.raises(RateLimitExceeded):
        await rate_limiter.check_rate_limit(client_id)

@pytest.mark.asyncio
async def test_metrics_collection(rate_limiter, sample_limits):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        limit = sample_limits[0]
        await rate_limiter.register_limit(limit)
        
        # Make some requests
        for _ in range(5):
            await rate_limiter.check_rate_limit(limit.client_id)
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_gauge.assert_called()

@pytest.mark.asyncio
async def test_cleanup(rate_limiter):
    # Add request data
    client_id = "cleanup_test"
    old_time = datetime.utcnow() - timedelta(minutes=10)
    
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = old_time
        await rate_limiter.track_request(client_id)
    
    # Run cleanup
    await rate_limiter.cleanup()
    
    stats = await rate_limiter.get_client_stats(client_id)
    assert stats.request_count == 0

@pytest.mark.asyncio
async def test_rate_limit_persistence(rate_limiter):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        await rate_limiter.save_state()
        mock_file.write.assert_called_once()
        
        await rate_limiter.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_rate_metrics_calculation(rate_limiter):
    client_id = "metrics_test"
    
    # Track requests over time
    start_time = datetime.utcnow()
    
    with patch('datetime.datetime') as mock_datetime:
        for i in range(60):
            mock_datetime.utcnow.return_value = start_time + timedelta(seconds=i)
            await rate_limiter.track_request(client_id)
    
    metrics = await rate_limiter.calculate_metrics(client_id)
    assert isinstance(metrics, RateLimitMetrics)
    assert abs(metrics.requests_per_second - 1.0) < 0.1

@pytest.mark.asyncio
async def test_adaptive_rate_limiting(rate_limiter):
    client_id = "adaptive_client"
    
    # Initialize with adaptive limits
    await rate_limiter.register_adaptive_limit(
        client_id=client_id,
        initial_rate=100,
        min_rate=50,
        max_rate=200
    )
    
    # Simulate high error rate
    for _ in range(10):
        await rate_limiter.record_error(client_id)
    
    # Rate should be reduced
    limit = rate_limiter.client_limits[client_id]
    assert limit.rate < 100

@pytest.mark.asyncio
async def test_client_quota_management(rate_limiter):
    client_id = "quota_client"
    
    # Set daily quota
    await rate_limiter.set_quota(
        client_id=client_id,
        daily_quota=1000
    )
    
    # Use some quota
    for _ in range(500):
        await rate_limiter.check_quota(client_id)
    
    quota_info = await rate_limiter.get_quota_info(client_id)
    assert quota_info.remaining == 500

@pytest.mark.asyncio
async def test_rate_limit_groups(rate_limiter):
    group_id = "api_group"
    clients = ["client1", "client2", "client3"]
    
    # Create group rate limit
    await rate_limiter.create_limit_group(
        group_id=group_id,
        rate=100,
        clients=clients
    )
    
    # Check that all clients share the limit
    for client_id in clients:
        for _ in range(33):  # Each client uses 33 requests
            await rate_limiter.check_rate_limit(client_id)
    
    # Next request should fail for any client
    with pytest.raises(RateLimitExceeded):
        await rate_limiter.check_rate_limit(clients[0]) 