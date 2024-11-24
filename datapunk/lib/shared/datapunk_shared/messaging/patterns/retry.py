from typing import Optional, Dict, Any, Callable, TypeVar, Generic, Union
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
import random
from enum import Enum
from ...monitoring import MetricsCollector

T = TypeVar('T')
R = TypeVar('R')

class RetryStrategy(Enum):
    """Available retry strategies"""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    RANDOM = "random"
    FIBONACCI = "fibonacci"

@dataclass
class RetryConfig:
    """Configuration for retry handling"""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True
    jitter_factor: float = 0.1
    timeout: Optional[float] = None
    backoff_base: float = 2.0
    retry_on_exceptions: tuple = (Exception,)
    retry_on_results: Optional[Callable[[Any], bool]] = None

class RetryState:
    """Tracks state for retry operations"""
    def __init__(self):
        self.attempts: int = 0
        self.first_attempt: Optional[datetime] = None
        self.last_attempt: Optional[datetime] = None
        self.last_delay: float = 0
        self.last_error: Optional[Exception] = None
        self.total_delay: float = 0
        self.fibonacci_prev: int = 1
        self.fibonacci_curr: int = 1

class RetryHandler(Generic[T, R]):
    """Handles retry logic with various strategies"""
    def __init__(
        self,
        config: RetryConfig,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.metrics = metrics_collector
        self._state = RetryState()

    async def execute(
        self,
        operation: Callable[..., R],
        *args,
        **kwargs
    ) -> R:
        """Execute operation with retry logic"""
        while True:
            try:
                if self._state.attempts == 0:
                    self._state.first_attempt = datetime.utcnow()

                self._state.attempts += 1
                self._state.last_attempt = datetime.utcnow()

                # Execute with timeout if configured
                if self.config.timeout:
                    result = await asyncio.wait_for(
                        operation(*args, **kwargs),
                        timeout=self.config.timeout
                    )
                else:
                    result = await operation(*args, **kwargs)

                # Check result if validator provided
                if self.config.retry_on_results and self.config.retry_on_results(result):
                    raise RetryableResultError(f"Retry condition met for result: {result}")

                # Success - record metrics and return
                if self.metrics:
                    await self._record_success_metrics()
                return result

            except asyncio.TimeoutError as e:
                self._state.last_error = e
                if self.metrics:
                    await self._record_error_metrics("timeout")
                await self._handle_retry(e)

            except self.config.retry_on_exceptions as e:
                self._state.last_error = e
                if self.metrics:
                    await self._record_error_metrics(e.__class__.__name__)
                await self._handle_retry(e)

    async def _handle_retry(self, error: Exception):
        """Handle retry logic and delays"""
        if self._state.attempts >= self.config.max_attempts:
            if self.metrics:
                await self.metrics.increment(
                    "retry.max_attempts_reached",
                    tags={"error": error.__class__.__name__}
                )
            raise MaxRetriesExceededError(
                f"Max retry attempts ({self.config.max_attempts}) reached",
                original_error=error,
                retry_state=self._state
            )

        delay = self._calculate_delay()
        
        # Apply jitter if enabled
        if self.config.jitter:
            jitter_range = delay * self.config.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)

        delay = min(delay, self.config.max_delay)
        self._state.last_delay = delay
        self._state.total_delay += delay

        if self.metrics:
            await self.metrics.timing(
                "retry.delay",
                delay,
                tags={"attempt": self._state.attempts}
            )

        await asyncio.sleep(delay)

    def _calculate_delay(self) -> float:
        """Calculate delay based on retry strategy"""
        attempt = self._state.attempts
        base_delay = self.config.initial_delay

        if self.config.strategy == RetryStrategy.FIXED:
            return base_delay

        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            return base_delay * (self.config.backoff_base ** (attempt - 1))

        elif self.config.strategy == RetryStrategy.LINEAR:
            return base_delay * attempt

        elif self.config.strategy == RetryStrategy.RANDOM:
            max_delay = base_delay * (self.config.backoff_base ** (attempt - 1))
            return random.uniform(base_delay, max_delay)

        elif self.config.strategy == RetryStrategy.FIBONACCI:
            # Calculate next Fibonacci number
            next_fib = self._state.fibonacci_curr + self._state.fibonacci_prev
            self._state.fibonacci_prev = self._state.fibonacci_curr
            self._state.fibonacci_curr = next_fib
            return base_delay * self._state.fibonacci_curr

        return base_delay

    async def _record_success_metrics(self):
        """Record success metrics"""
        if not self.metrics:
            return

        await self.metrics.increment(
            "retry.success",
            tags={"attempts": self._state.attempts}
        )
        
        if self._state.attempts > 1:
            await self.metrics.timing(
                "retry.recovery_time",
                (datetime.utcnow() - self._state.first_attempt).total_seconds(),
                tags={"attempts": self._state.attempts}
            )

    async def _record_error_metrics(self, error_type: str):
        """Record error metrics"""
        if not self.metrics:
            return

        await self.metrics.increment(
            "retry.error",
            tags={
                "error": error_type,
                "attempt": self._state.attempts
            }
        )

class RetryableResultError(Exception):
    """Error for retryable results"""
    pass

class MaxRetriesExceededError(Exception):
    """Error when max retries are exceeded"""
    def __init__(
        self,
        message: str,
        original_error: Exception,
        retry_state: RetryState
    ):
        super().__init__(message)
        self.original_error = original_error
        self.retry_state = retry_state
        self.attempts = retry_state.attempts
        self.total_delay = retry_state.total_delay 