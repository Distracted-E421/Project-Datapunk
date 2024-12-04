from typing import Optional, Dict, Tuple
import time
import structlog
from dataclasses import dataclass
from ..cache import CacheClient
from ..monitoring import MetricsClient

logger = structlog.get_logger()

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    window_seconds: int = 60
    max_requests: int = 1000
    burst_multiplier: float = 1.5
    cache_prefix: str = "ratelimit:"

class RateLimiter:
    """Token bucket rate limiter with Redis backend."""
    
    def __init__(self,
                 cache_client: CacheClient,
                 metrics: MetricsClient,
                 config: RateLimitConfig = RateLimitConfig()):
        self.cache = cache_client
        self.metrics = metrics
        self.config = config
        self.logger = logger.bind(component="rate_limiter")
    
    async def check_rate_limit(self,
                             key: str,
                             cost: int = 1) -> Tuple[bool, Dict]:
        """Check if request should be rate limited."""
        try:
            cache_key = f"{self.config.cache_prefix}{key}"
            current_time = int(time.time())
            window_start = current_time - self.config.window_seconds
            
            # Get current bucket
            bucket = await self.cache.get(cache_key) or {
                "tokens": self.config.max_requests,
                "last_update": current_time
            }
            
            # Calculate token replenishment
            time_passed = current_time - bucket["last_update"]
            tokens_to_add = (time_passed * self.config.max_requests 
                           // self.config.window_seconds)
            
            # Update bucket
            new_tokens = min(
                bucket["tokens"] + tokens_to_add,
                int(self.config.max_requests * self.config.burst_multiplier)
            )
            
            if new_tokens < cost:
                self.metrics.increment("rate_limit_exceeded", {"key": key})
                return False, {
                    "limit": self.config.max_requests,
                    "remaining": 0,
                    "reset": window_start + self.config.window_seconds,
                    "retry_after": (cost - new_tokens) * self.config.window_seconds 
                                 // self.config.max_requests
                }
            
            # Update bucket state
            bucket.update({
                "tokens": new_tokens - cost,
                "last_update": current_time
            })
            await self.cache.set(cache_key, bucket, self.config.window_seconds)
            
            self.metrics.increment("rate_limit_checked", {"key": key})
            return True, {
                "limit": self.config.max_requests,
                "remaining": new_tokens - cost,
                "reset": window_start + self.config.window_seconds
            }
            
        except Exception as e:
            self.logger.error("rate_limit_check_failed",
                            key=key,
                            error=str(e))
            # Fail open to prevent service disruption
            return True, {
                "limit": self.config.max_requests,
                "remaining": self.config.max_requests,
                "reset": int(time.time()) + self.config.window_seconds
            } 