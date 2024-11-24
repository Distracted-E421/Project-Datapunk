from typing import Optional, Dict, Any, Callable, TypeVar, Generic
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from enum import Enum
import random
from ...monitoring import MetricsCollector

T = TypeVar('T')

class RetryStrategy(Enum):
    """Retry strategies"""
    FIXED = "fixed"           # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"         # Linear backoff
    RANDOM = "random"         # Random delay within range
    FIBONACCI = "fibonacci"   # Fibonacci sequence delay

@dataclass
class RetryConfig:
    """Configuration for retry policy"""
    max_retries: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: float = 0.1  # Add randomness to delay
    timeout: float = 60.0  # Overall timeout
    retry_on_exceptions: tuple = (Exception,)
    retry_on_status_codes: Optional[set] = None
    backoff_factor: float = 2.0  # For exponential/linear backoff

class RetryError(Exception):
    """Base class for retry errors"""
    pass

class RetryTimeoutError(RetryError):
    """Error when retry timeout is exceeded"""
    pass

class RetryExhaustedError(RetryError):
    """Error when max retries are exhausted"""
    pass

class RetryPolicy(Generic[T]):
    """Implements retry patterns with various strategies"""
    def __init__(
        self,
        config: RetryConfig,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.metrics = metrics_collector

    def wrap(self, operation: Callable[..., T]) -> Callable[..., T]:
        """Wrap operation with retry logic"""
        async def wrapped(*args, **kwargs) -> T:
            start_time = datetime.utcnow()
            attempt = 0
            last_error = None

            while True:
                try:
                    attempt += 1
                    result = await operation(*args, **kwargs)

                    # Check status code if provided
                    if (
                        self.config.retry_on_status_codes and
                        hasattr(result, 'status_code') and
                        result.status_code in self.config.retry_on_status_codes
                    ):
                        raise RetryError(f"Status code {result.status_code} requires retry")

                    # Success - record metrics and return
                    if self.metrics:
                        await self.metrics.increment(
                            "retry.success",
                            tags={
                                "attempts": attempt,
                                "strategy": self.config.strategy.value
                            }
                        )
                    return result

                except self.config.retry_on_exceptions as e:
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    last_error = e

                    # Check timeout
                    if elapsed >= self.config.timeout:
                        if self.metrics:
                            await self.metrics.increment(
                                "retry.timeout",
                                tags={"error": str(e)}
                            )
                        raise RetryTimeoutError(
                            f"Operation timed out after {elapsed:.1f}s"
                        ) from e

                    # Check max retries
                    if attempt >= self.config.max_retries:
                        if self.metrics:
                            await self.metrics.increment(
                                "retry.exhausted",
                                tags={"error": str(e)}
                            )
                        raise RetryExhaustedError(
                            f"Max retries ({self.config.max_retries}) exceeded"
                        ) from e

                    # Calculate delay for next attempt
                    delay = self._calculate_delay(attempt)
                    
                    if self.metrics:
                        await self.metrics.increment(
                            "retry.attempt",
                            tags={
                                "attempt": attempt,
                                "delay": delay,
                                "error": str(e)
                            }
                        )
                    
                    # Wait before next attempt
                    await asyncio.sleep(delay)

        return wrapped

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay based on retry strategy"""
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.initial_delay

        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.initial_delay * (
                self.config.backoff_factor ** (attempt - 1)
            )

        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.initial_delay * attempt

        elif self.config.strategy == RetryStrategy.RANDOM:
            max_delay = min(
                self.config.initial_delay * attempt,
                self.config.max_delay
            )
            delay = random.uniform(0, max_delay)

        elif self.config.strategy == RetryStrategy.FIBONACCI:
            delay = self._fibonacci_delay(attempt)

        # Apply jitter
        if self.config.jitter > 0:
            jitter = random.uniform(
                -self.config.jitter * delay,
                self.config.jitter * delay
            )
            delay += jitter

        # Ensure delay doesn't exceed max_delay
        return min(delay, self.config.max_delay)

    def _fibonacci_delay(self, attempt: int) -> float:
        """Calculate Fibonacci sequence delay"""
        def fib(n: int) -> int:
            if n <= 0:
                return 0
            elif n == 1:
                return 1
            return fib(n - 1) + fib(n - 2)

        return self.config.initial_delay * fib(attempt)

    async def get_stats(self) -> Dict[str, Any]:
        """Get retry statistics"""
        if not self.metrics:
            return {}

        return {
            "total_retries": await self.metrics.get_count("retry.attempt"),
            "successful_retries": await self.metrics.get_count("retry.success"),
            "timeouts": await self.metrics.get_count("retry.timeout"),
            "exhausted": await self.metrics.get_count("retry.exhausted"),
            "strategy": self.config.strategy.value,
            "max_retries": self.config.max_retries,
            "timeout": self.config.timeout
        } 