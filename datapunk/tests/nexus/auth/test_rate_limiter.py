import pytest
import time
from src.nexus.auth.rate_limiter import RateLimiter, RateLimitType, RateLimit

@pytest.fixture
def rate_limiter():
    return RateLimiter()

def test_default_limits(rate_limiter):
    # Check default login attempt limit
    assert rate_limiter._limits[RateLimitType.LOGIN_ATTEMPT].max_attempts == 5
    assert rate_limiter._limits[RateLimitType.LOGIN_ATTEMPT].window_seconds == 300
    
    # Check default token generation limit
    assert rate_limiter._limits[RateLimitType.TOKEN_GENERATION].max_attempts == 10
    assert rate_limiter._limits[RateLimitType.TOKEN_GENERATION].window_seconds == 60
    
    # Check default API call limit
    assert rate_limiter._limits[RateLimitType.API_CALL].max_attempts == 100
    assert rate_limiter._limits[RateLimitType.API_CALL].window_seconds == 60

def test_configure_limit(rate_limiter):
    rate_limiter.configure_limit(
        RateLimitType.LOGIN_ATTEMPT,
        max_attempts=3,
        window_seconds=60,
        block_duration_seconds=1800
    )
    
    limit = rate_limiter._limits[RateLimitType.LOGIN_ATTEMPT]
    assert limit.max_attempts == 3
    assert limit.window_seconds == 60
    assert limit.block_duration_seconds == 1800

def test_rate_limiting(rate_limiter):
    # Configure a strict limit for testing
    rate_limiter.configure_limit(
        RateLimitType.LOGIN_ATTEMPT,
        max_attempts=2,
        window_seconds=60,
        block_duration_seconds=1
    )
    
    identifier = "test_user"
    
    # First attempt should succeed
    allowed, _ = rate_limiter.record_attempt(identifier, RateLimitType.LOGIN_ATTEMPT)
    assert allowed is True
    
    # Second attempt should succeed
    allowed, _ = rate_limiter.record_attempt(identifier, RateLimitType.LOGIN_ATTEMPT)
    assert allowed is True
    
    # Third attempt should fail and trigger block
    allowed, block_time = rate_limiter.record_attempt(identifier, RateLimitType.LOGIN_ATTEMPT)
    assert allowed is False
    assert block_time is not None
    
    # Verify blocked status
    blocked, remaining = rate_limiter.is_blocked(identifier, RateLimitType.LOGIN_ATTEMPT)
    assert blocked is True
    assert remaining is not None

def test_block_expiry(rate_limiter):
    # Configure a short block duration for testing
    rate_limiter.configure_limit(
        RateLimitType.LOGIN_ATTEMPT,
        max_attempts=1,
        window_seconds=60,
        block_duration_seconds=1  # 1 second block
    )
    
    identifier = "test_user"
    
    # Exceed limit to trigger block
    rate_limiter.record_attempt(identifier, RateLimitType.LOGIN_ATTEMPT)
    allowed, _ = rate_limiter.record_attempt(identifier, RateLimitType.LOGIN_ATTEMPT)
    assert allowed is False
    
    # Wait for block to expire
    time.sleep(1.1)
    
    # Should be allowed again
    blocked, _ = rate_limiter.is_blocked(identifier, RateLimitType.LOGIN_ATTEMPT)
    assert blocked is False

def test_reset(rate_limiter):
    identifier = "test_user"
    
    # Record some attempts
    rate_limiter.record_attempt(identifier, RateLimitType.LOGIN_ATTEMPT)
    rate_limiter.record_attempt(identifier, RateLimitType.LOGIN_ATTEMPT)
    
    # Reset attempts
    rate_limiter.reset(identifier, RateLimitType.LOGIN_ATTEMPT)
    
    # Check remaining attempts is back to max
    remaining = rate_limiter.get_remaining_attempts(identifier, RateLimitType.LOGIN_ATTEMPT)
    assert remaining == rate_limiter._limits[RateLimitType.LOGIN_ATTEMPT].max_attempts

def test_remaining_attempts(rate_limiter):
    rate_limiter.configure_limit(
        RateLimitType.API_CALL,
        max_attempts=5,
        window_seconds=60
    )
    
    identifier = "test_user"
    
    # Check initial remaining attempts
    remaining = rate_limiter.get_remaining_attempts(identifier, RateLimitType.API_CALL)
    assert remaining == 5
    
    # Record some attempts
    rate_limiter.record_attempt(identifier, RateLimitType.API_CALL)
    rate_limiter.record_attempt(identifier, RateLimitType.API_CALL)
    
    # Check remaining attempts
    remaining = rate_limiter.get_remaining_attempts(identifier, RateLimitType.API_CALL)
    assert remaining == 3

def test_window_expiry(rate_limiter):
    # Configure a short window for testing
    rate_limiter.configure_limit(
        RateLimitType.API_CALL,
        max_attempts=1,
        window_seconds=1  # 1 second window
    )
    
    identifier = "test_user"
    
    # Record attempt
    rate_limiter.record_attempt(identifier, RateLimitType.API_CALL)
    
    # Verify no remaining attempts
    remaining = rate_limiter.get_remaining_attempts(identifier, RateLimitType.API_CALL)
    assert remaining == 0
    
    # Wait for window to expire
    time.sleep(1.1)
    
    # Should have full attempts available again
    remaining = rate_limiter.get_remaining_attempts(identifier, RateLimitType.API_CALL)
    assert remaining == 1 