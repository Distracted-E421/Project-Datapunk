"""
Rate Limiting Strategy for Circuit Breaker

Implements a rate limiting strategy that controls request rates using multiple
algorithms and adapts limits based on system load and performance metrics.
"""

from typing import Dict, Optional, Any, List
import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog
from enum import Enum

logger = structlog.get_logger()

class RateLimitAlgorithm(Enum):
    """Available rate limiting algorithms"""
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    ADAPTIVE = "adaptive"

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.ADAPTIVE
    requests_per_second: float = 100.0
    burst_size: int = 50
    window_size_seconds: float = 1.0
    min_rate: float = 10.0
    max_rate: float = 1000.0
    scale_factor: float = 1.5
    cooldown_seconds: float = 60.0

class TokenBucket:
    """Token bucket rate limiter implementation"""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
        
    async def acquire(self) -> bool:
        """Try to acquire a token"""
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
            
    def update_rate(self, new_rate: float):
        """Update token generation rate"""
        self.rate = new_rate

class LeakyBucket:
    """Leaky bucket rate limiter implementation"""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.water_level = 0
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
        
    async def acquire(self) -> bool:
        """Try to add request to bucket"""
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            leaked = elapsed * self.rate
            self.water_level = max(0, self.water_level - leaked)
            self.last_update = now
            
            if self.water_level < self.capacity:
                self.water_level += 1
                return True
            return False
            
    def update_rate(self, new_rate: float):
        """Update leak rate"""
        self.rate = new_rate

class FixedWindow:
    """Fixed window rate limiter implementation"""
    
    def __init__(self, limit: int, window_seconds: float):
        self.limit = limit
        self.window_seconds = window_seconds
        self.current_window = 0
        self.request_count = 0
        self.lock = asyncio.Lock()
        
    async def acquire(self) -> bool:
        """Try to add request to current window"""
        async with self.lock:
            now = int(time.monotonic() / self.window_seconds)
            
            if now > self.current_window:
                self.current_window = now
                self.request_count = 0
                
            if self.request_count < self.limit:
                self.request_count += 1
                return True
            return False
            
    def update_limit(self, new_limit: int):
        """Update request limit"""
        self.limit = new_limit

class SlidingWindow:
    """Sliding window rate limiter implementation"""
    
    def __init__(self, limit: int, window_seconds: float):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: List[float] = []
        self.lock = asyncio.Lock()
        
    async def acquire(self) -> bool:
        """Try to add request to sliding window"""
        async with self.lock:
            now = time.monotonic()
            window_start = now - self.window_seconds
            
            # Remove old requests
            while self.requests and self.requests[0] <= window_start:
                self.requests.pop(0)
                
            if len(self.requests) < self.limit:
                self.requests.append(now)
                return True
            return False
            
    def update_limit(self, new_limit: int):
        """Update request limit"""
        self.limit = new_limit

class RateLimitingStrategy:
    """
    Adaptive rate limiting strategy that combines multiple algorithms
    and adjusts limits based on system performance.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize rate limiting strategy"""
        self.config = config or RateLimitConfig()
        self.logger = logger.bind(component="rate_limiting_strategy")
        
        # Initialize limiters
        self.token_bucket = TokenBucket(
            self.config.requests_per_second,
            self.config.burst_size
        )
        self.leaky_bucket = LeakyBucket(
            self.config.requests_per_second,
            self.config.burst_size
        )
        self.fixed_window = FixedWindow(
            int(self.config.requests_per_second * self.config.window_size_seconds),
            self.config.window_size_seconds
        )
        self.sliding_window = SlidingWindow(
            int(self.config.requests_per_second * self.config.window_size_seconds),
            self.config.window_size_seconds
        )
        
        # Performance tracking
        self.success_count = 0
        self.failure_count = 0
        self.last_adjustment = time.monotonic()
        self.current_rate = self.config.requests_per_second
        
    async def should_allow_request(self) -> bool:
        """Determine if request should be allowed based on rate limits"""
        if self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return await self.token_bucket.acquire()
        elif self.config.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
            return await self.leaky_bucket.acquire()
        elif self.config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return await self.fixed_window.acquire()
        elif self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return await self.sliding_window.acquire()
        else:  # Adaptive
            # Try all algorithms and use most permissive
            results = await asyncio.gather(
                self.token_bucket.acquire(),
                self.leaky_bucket.acquire(),
                self.fixed_window.acquire(),
                self.sliding_window.acquire()
            )
            return any(results)
            
    async def record_success(self):
        """Record successful request"""
        self.success_count += 1
        await self._adjust_rate()
        
    async def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        await self._adjust_rate()
        
    async def _adjust_rate(self):
        """Adjust rate limits based on performance metrics"""
        now = time.monotonic()
        if now - self.last_adjustment < self.config.cooldown_seconds:
            return
            
        total = self.success_count + self.failure_count
        if total == 0:
            return
            
        error_rate = self.failure_count / total
        
        # Adjust rate based on error rate
        if error_rate > 0.1:  # More than 10% errors
            self.current_rate = max(
                self.config.min_rate,
                self.current_rate / self.config.scale_factor
            )
        elif error_rate < 0.01:  # Less than 1% errors
            self.current_rate = min(
                self.config.max_rate,
                self.current_rate * self.config.scale_factor
            )
            
        # Update all limiters
        self.token_bucket.update_rate(self.current_rate)
        self.leaky_bucket.update_rate(self.current_rate)
        self.fixed_window.update_limit(
            int(self.current_rate * self.config.window_size_seconds)
        )
        self.sliding_window.update_limit(
            int(self.current_rate * self.config.window_size_seconds)
        )
        
        # Reset counters
        self.success_count = 0
        self.failure_count = 0
        self.last_adjustment = now
        
        self.logger.info(
            "Rate limit adjusted",
            new_rate=self.current_rate,
            error_rate=error_rate
        )
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiting metrics"""
        total = self.success_count + self.failure_count
        error_rate = self.failure_count / total if total > 0 else 0
        
        return {
            "algorithm": self.config.algorithm.value,
            "current_rate": self.current_rate,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "error_rate": error_rate,
            "last_adjustment": self.last_adjustment
        } 