"""
Service Mesh Rate Limiting System

Implements distributed rate limiting for the Datapunk service mesh using
a token bucket algorithm with sliding window support. Provides protection
against service abuse while ensuring fair resource allocation.

Key features:
- Token bucket rate limiting
- Sliding window counting
- Burst handling
- Distributed state management
- Real-time metric integration

See sys-arch.mmd Gateway/RateLimiting for implementation details.
"""

from typing import Dict, Optional, Tuple
import time
import asyncio
import logging
from dataclasses import dataclass
from collections import defaultdict
from .auth_metrics import AuthMetrics

@dataclass
class RateLimitConfig:
    """
    Rate limit configuration parameters.
    
    Defines service-specific rate limiting rules with support for
    burst handling and sliding windows.
    
    NOTE: Window size affects memory usage - larger windows require
    more state tracking.
    """
    requests_per_second: int
    burst_size: int
    window_size: int = 60  # seconds

class TokenBucket:
    """
    Token bucket rate limiter implementation.
    
    Uses token bucket algorithm for rate limiting with support for
    burst handling. Tokens are replenished continuously rather than
    at fixed intervals for smoother traffic flow.
    
    TODO: Add support for priority-based token allocation
    FIXME: Improve thread safety for token updates
    """
    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket with rate and capacity.
        
        NOTE: Rate is in tokens per second, capacity determines
        maximum burst size.
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()

    def try_consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens from the bucket.
        
        Updates token count based on time elapsed since last check,
        then attempts to consume requested tokens.
        
        NOTE: Token replenishment is calculated on-demand to avoid
        background processing overhead.
        """
        now = time.time()
        # Replenish tokens based on elapsed time
        self.tokens = min(
            self.capacity,
            self.tokens + self.rate * (now - self.last_update)
        )
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

class RateLimiter:
    """
    Service mesh rate limiting coordinator.
    
    Manages rate limiting across the service mesh, combining token
    bucket and sliding window approaches for robust protection.
    
    TODO: Add distributed rate limit synchronization
    TODO: Implement rate limit policy inheritance
    """
    def __init__(
        self,
        metrics_enabled: bool = True
    ):
        """
        Initialize rate limiter with optional metrics.
        
        NOTE: Metrics are recommended for production deployments
        to monitor rate limit effectiveness.
        """
        self.buckets: Dict[str, TokenBucket] = {}
        self.configs: Dict[str, RateLimitConfig] = {}
        self.request_counts: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self.logger = logging.getLogger(__name__)
        self.metrics = AuthMetrics() if metrics_enabled else None

    async def configure_limit(
        self,
        service_id: str,
        config: RateLimitConfig
    ) -> None:
        """
        Configure rate limiting for a service.
        
        Sets up both token bucket and sliding window limiters
        for comprehensive rate control.
        
        NOTE: Changes take effect immediately for new requests.
        """
        self.configs[service_id] = config
        self.buckets[service_id] = TokenBucket(
            rate=config.requests_per_second,
            capacity=config.burst_size
        )

    async def check_rate_limit(
        self,
        service_id: str,
        current_time: Optional[float] = None
    ) -> Tuple[bool, Optional[float]]:
        """
        Validate request against rate limits.
        
        Applies both token bucket and sliding window checks:
        1. Token bucket for precise rate control
        2. Sliding window for burst protection
        
        Returns (allowed, retry_after) tuple where retry_after
        indicates when the request might succeed.
        
        NOTE: Fails open if rate limiting is not configured to
        prevent accidental service disruption.
        """
        try:
            if service_id not in self.configs:
                return True, None

            current_time = current_time or time.time()
            config = self.configs[service_id]
            bucket = self.buckets[service_id]
            current_window = int(current_time / config.window_size)

            # Clean up expired window data
            self.request_counts[service_id] = {
                window: count
                for window, count in self.request_counts[service_id].items()
                if window >= current_window - 1
            }

            # Apply token bucket check
            if not bucket.try_consume():
                if self.metrics:
                    await self.metrics.record_rate_limit_exceeded(service_id)
                return False, self._calculate_retry_after(bucket)

            # Update and check sliding window
            self.request_counts[service_id][current_window] += 1

            if self.request_counts[service_id][current_window] > config.requests_per_second * config.window_size:
                if self.metrics:
                    await self.metrics.record_rate_limit_exceeded(service_id)
                return False, self._calculate_retry_after(bucket)

            if self.metrics:
                await self.metrics.record_request_allowed(service_id)
            return True, None

        except Exception as e:
            self.logger.error(f"Rate limit check failed for {service_id}: {str(e)}")
            return True, None  # Fail open for safety

    def _calculate_retry_after(self, bucket: TokenBucket) -> float:
        """
        Calculate wait time for next request.
        
        Estimates time until sufficient tokens will be available
        based on current token count and replenishment rate.
        
        NOTE: This is an estimate and may be affected by other
        requests arriving before retry.
        """
        if bucket.tokens <= 0:
            return (1 - bucket.tokens) / bucket.rate
        return 0.0

    async def get_current_usage(self, service_id: str) -> Dict[str, float]:
        """Get current rate limit usage statistics"""
        try:
            if service_id not in self.configs:
                return {}

            current_time = time.time()
            current_window = int(current_time / self.configs[service_id].window_size)
            current_count = self.request_counts[service_id][current_window]

            return {
                'current_rate': current_count / self.configs[service_id].window_size,
                'burst_capacity': self.buckets[service_id].tokens,
                'window_requests': current_count
            }

        except Exception as e:
            self.logger.error(f"Failed to get usage stats for {service_id}: {str(e)}")
            return {} 