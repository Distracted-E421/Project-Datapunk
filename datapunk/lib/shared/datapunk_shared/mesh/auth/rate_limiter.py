from typing import Dict, Optional, Tuple
import time
import asyncio
import logging
from dataclasses import dataclass
from collections import defaultdict
from .auth_metrics import AuthMetrics

@dataclass
class RateLimitConfig:
    requests_per_second: int
    burst_size: int
    window_size: int = 60  # seconds

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()

    def try_consume(self, tokens: int = 1) -> bool:
        now = time.time()
        # Add tokens based on time passed
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
    def __init__(
        self,
        metrics_enabled: bool = True
    ):
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
        """Configure rate limit for a service"""
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
        """Check if request is within rate limits"""
        try:
            if service_id not in self.configs:
                return True, None

            current_time = current_time or time.time()
            config = self.configs[service_id]
            bucket = self.buckets[service_id]
            current_window = int(current_time / config.window_size)

            # Clean up old windows
            self.request_counts[service_id] = {
                window: count
                for window, count in self.request_counts[service_id].items()
                if window >= current_window - 1
            }

            # Check token bucket
            if not bucket.try_consume():
                if self.metrics:
                    await self.metrics.record_rate_limit_exceeded(service_id)
                return False, self._calculate_retry_after(bucket)

            # Update request count
            self.request_counts[service_id][current_window] += 1

            # Check window limit
            if self.request_counts[service_id][current_window] > config.requests_per_second * config.window_size:
                if self.metrics:
                    await self.metrics.record_rate_limit_exceeded(service_id)
                return False, self._calculate_retry_after(bucket)

            if self.metrics:
                await self.metrics.record_request_allowed(service_id)
            return True, None

        except Exception as e:
            self.logger.error(f"Rate limit check failed for {service_id}: {str(e)}")
            return True, None  # Fail open in case of errors

    def _calculate_retry_after(self, bucket: TokenBucket) -> float:
        """Calculate when the next request might be allowed"""
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