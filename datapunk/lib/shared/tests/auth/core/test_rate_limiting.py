"""
Core Rate Limiting Tests
-------------------

Tests the core rate limiting system including:
- Rate limit rules
- Token bucket algorithm
- Window tracking
- Limit enforcement
- Quota management
- Performance monitoring
- Security controls

Run with: pytest -v test_rate_limiting.py
"""

import pytest
from datetime import datetime, timedelta
import json
from unittest.mock import AsyncMock, Mock, patch

from datapunk_shared.auth.core.rate_limiting import (
    RateLimiter,
    RateLimit,
    TokenBucket,
    SlidingWindow,
    RateLimitRule,
    QuotaManager,
    LimitContext
)
from datapunk_shared.auth.core.exceptions import RateLimitError

# Test Fixtures

@pytest.fixture
def storage_client():
    """Mock storage client for testing."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.set = AsyncMock()
    client.increment = AsyncMock()
    return client

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.gauge = AsyncMock()
    return client

@pytest.fixture
def rate_limit():
    """Create rate limit for testing."""
    return RateLimit(
        requests=100,
        window=timedelta(minutes=1),
        burst=10
    )

@pytest.fixture
def rate_limiter(storage_client, metrics_client, rate_limit):
    """Create rate limiter for testing."""
    return RateLimiter(
        storage=storage_client,
        metrics=metrics_client,
        limit=rate_limit
    )

@pytest.fixture
def limit_context():
    """Create limit context for testing."""
    return LimitContext(
        user_id="test_user",
        resource="test_resource",
        action="test_action",
        timestamp=datetime.utcnow()
    )

# Rate Limit Tests

def test_rate_limit_creation():
    """Test rate limit creation."""
    limit = RateLimit(
        requests=100,
        window=timedelta(minutes=1)
    )
    
    assert limit.requests == 100
    assert limit.window.total_seconds() == 60
    assert limit.burst is None

def test_rate_limit_validation():
    """Test rate limit validation."""
    # Invalid requests
    with pytest.raises(ValueError):
        RateLimit(requests=0, window=timedelta(minutes=1))
    
    # Invalid window
    with pytest.raises(ValueError):
        RateLimit(requests=100, window=timedelta(seconds=0))
    
    # Invalid burst
    with pytest.raises(ValueError):
        RateLimit(requests=100, window=timedelta(minutes=1), burst=-1)

# Token Bucket Tests

def test_token_bucket():
    """Test token bucket algorithm."""
    bucket = TokenBucket(
        capacity=10,
        refill_rate=1,
        refill_time=timedelta(seconds=1)
    )
    
    # Initial state
    assert bucket.tokens == 10
    
    # Consume tokens
    assert bucket.consume(5) is True
    assert bucket.tokens == 5
    
    # Exceed capacity
    assert bucket.consume(6) is False
    assert bucket.tokens == 5

def test_bucket_refill():
    """Test token bucket refill."""
    bucket = TokenBucket(
        capacity=10,
        refill_rate=2,
        refill_time=timedelta(seconds=1)
    )
    
    # Consume tokens
    bucket.consume(8)
    assert bucket.tokens == 2
    
    # Wait for refill
    time.sleep(1)
    bucket.refill()
    assert bucket.tokens == 4  # 2 + 2 refilled

# Sliding Window Tests

def test_sliding_window():
    """Test sliding window algorithm."""
    window = SlidingWindow(
        size=timedelta(minutes=1),
        limit=10
    )
    
    # Add requests
    now = datetime.utcnow()
    for _ in range(5):
        window.add_request(now)
    
    assert window.get_request_count(now) == 5
    
    # Add more requests in next window
    future = now + timedelta(seconds=30)
    for _ in range(3):
        window.add_request(future)
    
    assert window.get_request_count(future) == 8

def test_window_expiration():
    """Test window request expiration."""
    window = SlidingWindow(
        size=timedelta(minutes=1),
        limit=10
    )
    
    # Add old requests
    past = datetime.utcnow() - timedelta(minutes=2)
    for _ in range(5):
        window.add_request(past)
    
    # Check current count
    now = datetime.utcnow()
    assert window.get_request_count(now) == 0  # Old requests expired

# Rate Limiter Tests

@pytest.mark.asyncio
async def test_rate_limiting(rate_limiter, limit_context):
    """Test rate limiting."""
    # Allow requests within limit
    for _ in range(10):
        result = await rate_limiter.check_limit(limit_context)
        assert result.allowed is True
    
    # Mock reaching limit
    rate_limiter.storage.get.return_value = 100  # Max requests
    
    result = await rate_limiter.check_limit(limit_context)
    assert result.allowed is False
    assert result.retry_after > 0

@pytest.mark.asyncio
async def test_burst_handling(rate_limiter, limit_context):
    """Test burst handling."""
    # Configure burst
    rate_limiter.limit.burst = 5
    
    # Allow burst
    for _ in range(5):
        result = await rate_limiter.check_limit(limit_context, burst=True)
        assert result.allowed is True
    
    # Exceed burst
    result = await rate_limiter.check_limit(limit_context, burst=True)
    assert result.allowed is False

# Quota Management Tests

def test_quota_management():
    """Test quota management."""
    quota = QuotaManager(
        daily_limit=1000,
        monthly_limit=10000
    )
    
    # Check quota
    assert quota.check_quota("test_user", 100) is True
    assert quota.get_remaining("test_user") == 900
    
    # Exceed quota
    assert quota.check_quota("test_user", 1000) is False

def test_quota_reset():
    """Test quota reset."""
    quota = QuotaManager(
        daily_limit=1000,
        reset_interval=timedelta(days=1)
    )
    
    # Use quota
    quota.check_quota("test_user", 500)
    
    # Mock time passing
    with patch("datetime.datetime") as mock_time:
        mock_time.utcnow.return_value = datetime.utcnow() + timedelta(days=1)
        assert quota.get_remaining("test_user") == 1000  # Reset

# Rule Management Tests

def test_rule_creation():
    """Test rate limit rule creation."""
    rule = RateLimitRule(
        name="api_limit",
        limit=RateLimit(requests=100, window=timedelta(minutes=1)),
        resources=["api/*"],
        user_type="standard"
    )
    
    assert rule.name == "api_limit"
    assert rule.limit.requests == 100
    assert "api/*" in rule.resources
    assert rule.user_type == "standard"

def test_rule_matching():
    """Test rate limit rule matching."""
    rule = RateLimitRule(
        name="api_limit",
        limit=RateLimit(requests=100, window=timedelta(minutes=1)),
        resources=["api/*"],
        user_type="standard"
    )
    
    # Match resource
    assert rule.matches_resource("api/users") is True
    assert rule.matches_resource("web/users") is False
    
    # Match user type
    assert rule.matches_user_type("standard") is True
    assert rule.matches_user_type("premium") is False

# Performance Tests

@pytest.mark.asyncio
async def test_limiter_performance(rate_limiter, limit_context):
    """Test rate limiter performance."""
    # Process multiple requests
    start_time = datetime.utcnow()
    for _ in range(1000):
        await rate_limiter.check_limit(limit_context)
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 1.0  # Should process 1000 checks within 1 second

@pytest.mark.asyncio
async def test_concurrent_limits():
    """Test concurrent rate limiting."""
    limiter = RateLimiter(
        limit=RateLimit(requests=100, window=timedelta(minutes=1))
    )
    
    # Simulate concurrent requests
    async def make_request():
        context = LimitContext(user_id=f"user_{i}")
        return await limiter.check_limit(context)
    
    tasks = [make_request() for i in range(100)]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 100
    assert all(r.allowed for r in results)

# Security Tests

@pytest.mark.asyncio
async def test_ddos_protection(rate_limiter):
    """Test DDoS protection."""
    # Configure stricter limits for suspicious activity
    rate_limiter.enable_ddos_protection(
        threshold=50,
        window=timedelta(seconds=10)
    )
    
    # Simulate rapid requests
    context = LimitContext(
        user_id="suspicious_user",
        ip_address="1.2.3.4"
    )
    
    for _ in range(60):  # Exceed threshold
        await rate_limiter.check_limit(context)
    
    # Verify blocking
    result = await rate_limiter.check_limit(context)
    assert result.allowed is False
    assert result.block_reason == "ddos_protection"

@pytest.mark.asyncio
async def test_abuse_detection(rate_limiter, limit_context):
    """Test abuse detection."""
    # Enable abuse detection
    rate_limiter.enable_abuse_detection()
    
    # Simulate suspicious pattern
    for _ in range(10):
        await rate_limiter.check_limit(limit_context)
        await asyncio.sleep(0.1)  # Very rapid requests
    
    # Verify detection
    result = await rate_limiter.check_limit(limit_context)
    assert result.allowed is False
    assert result.abuse_detected is True

# Metrics Collection Tests

@pytest.mark.asyncio
async def test_metrics_collection(rate_limiter, limit_context):
    """Test metrics collection."""
    await rate_limiter.check_limit(limit_context)
    
    # Verify metrics
    rate_limiter.metrics.increment.assert_has_calls([
        mock.call("rate_limit_checks", tags={"resource": "test_resource"}),
        mock.call("requests_processed", tags={"user_id": "test_user"})
    ])
    
    # Verify gauges
    rate_limiter.metrics.gauge.assert_called_with(
        "request_count",
        mock.ANY,
        tags={"resource": "test_resource"}
    )

@pytest.mark.asyncio
async def test_limit_tracking(rate_limiter):
    """Test limit tracking metrics."""
    # Track multiple resources
    contexts = [
        LimitContext(resource=f"resource_{i}")
        for i in range(5)
    ]
    
    for context in contexts:
        await rate_limiter.check_limit(context)
    
    # Verify tracking
    rate_limiter.metrics.gauge.assert_has_calls([
        mock.call("resource_usage", mock.ANY, tags={"resource": f"resource_{i}"})
        for i in range(5)
    ]) 