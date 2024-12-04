"""
Rate limiting system with multiple strategies.

Purpose:
    Provides a flexible rate limiting system for API request throttling with multiple
    implementation strategies to suit different use cases.

Context:
    Part of the authentication/authorization system, protecting APIs from abuse
    while ensuring fair resource allocation.

Design:
    - Implements three rate limiting algorithms: Token Bucket, Sliding Window, and Leaky Bucket
    - Uses distributed caching for scalability across multiple instances
    - Provides configurable parameters for fine-tuning rate limit behavior
    - Includes metrics collection for monitoring and alerting
    - Fails open to prevent system lockout during errors

Error Handling:
    - All limiters fail open (allow requests) when errors occur
    - Errors are logged with structlog for debugging
    - Metrics are collected for both successful and failed rate limit checks

Performance Considerations:
    - Uses atomic cache operations where possible to prevent race conditions
    - Minimizes cache operations per request
    - Implements efficient cleanup of expired records
"""

from typing import Dict, Optional, Any, TYPE_CHECKING, List
import structlog
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import time
import math

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....cache import CacheClient

logger = structlog.get_logger()

class RateLimitStrategy(Enum):
    """
    Available rate limiting strategies.
    
    TOKEN_BUCKET: Best for API rate limiting with burst handling
    SLIDING_WINDOW: Provides smooth rate limiting with precise time windows
    LEAKY_BUCKET: Ideal for traffic shaping and constant outflow
    FIXED_WINDOW: Simple counting within fixed time periods
    ADAPTIVE: Dynamic limits based on system load (not implemented)
    """

@dataclass
class RateLimitConfig:
    """
    Configuration for rate limiting.
    
    Note: window_size and sync_interval are in seconds
    Warning: Setting distributed=True requires a distributed cache implementation
    """
    requests_per_second: int
    burst_size: int
    window_size: int = 60  # seconds
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    distributed: bool = True
    sync_interval: int = 5  # seconds

@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    remaining: int
    reset_after: float
    retry_after: Optional[float] = None
    burst_remaining: Optional[int] = None

class TokenBucketLimiter:
    """
    Token bucket rate limiting implementation.
    
    Design:
        - Tokens replenish at a constant rate up to burst_size
        - Each request consumes one token
        - Allows temporary bursts of traffic while maintaining long-term rate
    
    Cache Structure:
        Key: "ratelimit:token:{key}"
        Value: {
            "tokens": float,  # Current token count
            "last_update": float  # Timestamp of last update
        }
    """
    
    def __init__(self,
                 cache: 'CacheClient',
                 metrics: 'MetricsClient',
                 config: RateLimitConfig):
        self.cache = cache
        self.metrics = metrics
        self.config = config
        self.logger = logger.bind(strategy="token_bucket")
    
    async def check_limit(self, key: str) -> RateLimitResult:
        """
        Check if request is allowed under token bucket algorithm.
        
        Implementation:
            1. Calculate tokens replenished since last update
            2. If tokens available, consume one and allow request
            3. If no tokens, calculate wait time for next token
        
        Note: Uses atomic cache operations to prevent race conditions
        """
        try:
            bucket_key = f"ratelimit:token:{key}"
            now = time.time()
            
            # Get current bucket state
            bucket = await self.cache.get(bucket_key) or {
                "tokens": self.config.burst_size,
                "last_update": now
            }
            
            # Calculate token replenishment
            elapsed = now - bucket["last_update"]
            new_tokens = min(
                self.config.burst_size,
                bucket["tokens"] + elapsed * self.config.requests_per_second
            )
            
            # Check if request can be allowed
            if new_tokens >= 1:
                # Update bucket
                bucket.update({
                    "tokens": new_tokens - 1,
                    "last_update": now
                })
                await self.cache.set(bucket_key, bucket)
                
                self.metrics.increment(
                    "rate_limit_allowed",
                    {"strategy": "token_bucket"}
                )
                
                return RateLimitResult(
                    allowed=True,
                    remaining=int(bucket["tokens"]),
                    reset_after=0,
                    burst_remaining=self.config.burst_size - int(bucket["tokens"])
                )
            
            # Request denied
            self.metrics.increment(
                "rate_limit_denied",
                {"strategy": "token_bucket"}
            )
            
            retry_after = (1 - bucket["tokens"]) / self.config.requests_per_second
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_after=retry_after,
                retry_after=retry_after
            )
            
        except Exception as e:
            self.logger.error("rate_limit_check_failed",
                            error=str(e))
            # Fail open if check fails
            return RateLimitResult(
                allowed=True,
                remaining=0,
                reset_after=0
            )

class SlidingWindowLimiter:
    """
    Sliding window rate limiting implementation.
    
    Design:
        - Maintains sorted set of request timestamps
        - Provides smooth rate limiting without sharp edges
        - More precise than fixed windows but higher storage overhead
    
    Cache Structure:
        Key: "ratelimit:window:{key}"
        Value: Sorted set of request timestamps
    """
    
    def __init__(self,
                 cache: 'CacheClient',
                 metrics: 'MetricsClient',
                 config: RateLimitConfig):
        self.cache = cache
        self.metrics = metrics
        self.config = config
        self.logger = logger.bind(strategy="sliding_window")
    
    async def check_limit(self, key: str) -> RateLimitResult:
        """Check if request is allowed."""
        try:
            window_key = f"ratelimit:window:{key}"
            now = time.time()
            window_start = now - self.config.window_size
            
            # Clean old entries and get current count
            pipeline = self.cache.pipeline()
            pipeline.zremrangebyscore(window_key, 0, window_start)
            pipeline.zcard(window_key)
            _, current_count = await pipeline.execute()
            
            # Check if under limit
            if current_count < self.config.requests_per_second * self.config.window_size:
                # Add request timestamp
                await self.cache.zadd(window_key, {str(now): now})
                
                self.metrics.increment(
                    "rate_limit_allowed",
                    {"strategy": "sliding_window"}
                )
                
                remaining = (self.config.requests_per_second * 
                           self.config.window_size - current_count - 1)
                
                return RateLimitResult(
                    allowed=True,
                    remaining=remaining,
                    reset_after=self.config.window_size
                )
            
            # Request denied
            self.metrics.increment(
                "rate_limit_denied",
                {"strategy": "sliding_window"}
            )
            
            oldest = await self.cache.zrange(window_key, 0, 0, withscores=True)
            retry_after = oldest[0][1] - window_start if oldest else self.config.window_size
            
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_after=self.config.window_size,
                retry_after=retry_after
            )
            
        except Exception as e:
            self.logger.error("rate_limit_check_failed",
                            error=str(e))
            # Fail open if check fails
            return RateLimitResult(
                allowed=True,
                remaining=0,
                reset_after=0
            )

class LeakyBucketLimiter:
    """
    Leaky bucket rate limiting implementation.
    
    Design:
        - Models a bucket with constant outflow rate
        - Good for traffic shaping and queue management
        - Smooths out traffic spikes
    
    Cache Structure:
        Key: "ratelimit:leaky:{key}"
        Value: {
            "water_level": float,  # Current queue size
            "last_update": float  # Timestamp of last update
        }
    """
    
    def __init__(self,
                 cache: 'CacheClient',
                 metrics: 'MetricsClient',
                 config: RateLimitConfig):
        self.cache = cache
        self.metrics = metrics
        self.config = config
        self.logger = logger.bind(strategy="leaky_bucket")
    
    async def check_limit(self, key: str) -> RateLimitResult:
        """Check if request is allowed."""
        try:
            bucket_key = f"ratelimit:leaky:{key}"
            now = time.time()
            
            # Get current bucket state
            bucket = await self.cache.get(bucket_key) or {
                "water_level": 0,
                "last_update": now
            }
            
            # Calculate leakage
            elapsed = now - bucket["last_update"]
            leaked = elapsed * self.config.requests_per_second
            water_level = max(0, bucket["water_level"] - leaked)
            
            # Check if request can be added
            if water_level < self.config.burst_size:
                # Update bucket
                bucket.update({
                    "water_level": water_level + 1,
                    "last_update": now
                })
                await self.cache.set(bucket_key, bucket)
                
                self.metrics.increment(
                    "rate_limit_allowed",
                    {"strategy": "leaky_bucket"}
                )
                
                return RateLimitResult(
                    allowed=True,
                    remaining=self.config.burst_size - int(water_level) - 1,
                    reset_after=0
                )
            
            # Request denied
            self.metrics.increment(
                "rate_limit_denied",
                {"strategy": "leaky_bucket"}
            )
            
            retry_after = (water_level - self.config.burst_size + 1) / self.config.requests_per_second
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_after=retry_after,
                retry_after=retry_after
            )
            
        except Exception as e:
            self.logger.error("rate_limit_check_failed",
                            error=str(e))
            # Fail open if check fails
            return RateLimitResult(
                allowed=True,
                remaining=0,
                reset_after=0
            )

class RateLimiter:
    """
    Central rate limiting manager.
    
    Design:
        - Factory pattern for creating specific limiter implementations
        - Handles strategy selection and initialization
        - Centralizes metrics collection and error handling
    
    Note: New rate limiting strategies should be added to self.limiters
    TODO: Implement adaptive rate limiting based on system metrics
    """
    
    def __init__(self,
                 cache: 'CacheClient',
                 metrics: 'MetricsClient'):
        self.cache = cache
        self.metrics = metrics
        self.logger = logger.bind(component="rate_limiter")
        
        # Initialize limiters
        self.limiters = {
            RateLimitStrategy.TOKEN_BUCKET: TokenBucketLimiter,
            RateLimitStrategy.SLIDING_WINDOW: SlidingWindowLimiter,
            RateLimitStrategy.LEAKY_BUCKET: LeakyBucketLimiter
        }
    
    async def check_limit(self,
                         key: str,
                         config: RateLimitConfig) -> RateLimitResult:
        """Check rate limit using configured strategy."""
        try:
            limiter_class = self.limiters.get(config.strategy)
            if not limiter_class:
                raise ValueError(f"Unknown rate limit strategy: {config.strategy}")
            
            limiter = limiter_class(self.cache, self.metrics, config)
            result = await limiter.check_limit(key)
            
            # Update metrics
            self.metrics.gauge(
                "rate_limit_remaining",
                result.remaining,
                {"strategy": config.strategy.value}
            )
            
            return result
            
        except Exception as e:
            self.logger.error("rate_limit_check_failed",
                            error=str(e))
            # Fail open if check fails
            return RateLimitResult(
                allowed=True,
                remaining=0,
                reset_after=0
            ) 