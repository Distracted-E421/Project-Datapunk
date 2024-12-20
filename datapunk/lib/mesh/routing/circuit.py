from typing import Optional, Dict, Any, Callable, TypeVar, Generic
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from ..monitoring import MetricsCollector

T = TypeVar('T')

"""
Circuit breaker implementation with adaptive timeout and health monitoring.

Implements the circuit breaker pattern to prevent cascading failures by:
- Monitoring operation success/failure rates
- Adaptively adjusting retry timeouts
- Providing graceful service degradation
- Collecting performance metrics

Design based on Martin Fowler's Circuit Breaker pattern with enhancements
for async operations and adaptive behavior.
"""

class CircuitState(Enum):
    """
    Circuit breaker states following finite state machine pattern:
    
    CLOSED -> Normal operation, monitoring for failures
    OPEN -> Failing fast, preventing further load
    HALF_OPEN -> Testing recovery with limited traffic
    
    NOTE: State transitions are thread-safe via async locks
    """
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitConfig:
    """
    Circuit breaker configuration with adaptive behavior controls.
    
    Key parameters:
    - failure_threshold: Failures before opening circuit
    - success_threshold: Successes needed to close circuit
    - error_rate_threshold: Error rate trigger (0.0-1.0)
    - cooldown_factor: Exponential backoff multiplier
    
    NOTE: Default values tuned for microservice environments
    TODO: Add per-service configuration support
    """
    failure_threshold: int = 5  # Number of failures before opening
    success_threshold: int = 2  # Number of successes before closing
    timeout: float = 60.0  # Seconds to wait before half-open
    window_size: int = 10  # Size of rolling window
    error_rate_threshold: float = 0.5  # Error rate to trigger opening
    min_throughput: int = 5  # Minimum requests before error rate check
    cooldown_factor: float = 2.0  # Multiply timeout by this on consecutive failures

class CircuitBreaker(Generic[T]):
    """
    Async circuit breaker with adaptive timeout and metrics collection.
    
    Features:
    - Rolling window error rate monitoring
    - Exponential backoff for repeated failures
    - Metric collection for monitoring
    - Thread-safe state transitions
    
    FIXME: Potential race condition in window updates
    TODO: Add circuit state persistence
    """
    def __init__(
        self,
        config: CircuitConfig,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.metrics = metrics_collector
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._consecutive_timeouts = 0
        self._request_window: List[bool] = []  # True for success, False for failure
        self._lock = asyncio.Lock()

    async def execute(
        self,
        operation: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Execute operation with circuit breaker protection.
        
        Handles:
        - State-based execution control
        - Success/failure tracking
        - Metric collection
        - Timeout management
        
        Raises CircuitOpenError if circuit is OPEN
        """
        async with self._lock:
            await self._check_state_transition()
            
            if self._state == CircuitState.OPEN:
                raise CircuitOpenError(
                    f"Circuit is OPEN. Failing fast. Try again in {self._get_remaining_timeout()} seconds"
                )

        try:
            result = await operation(*args, **kwargs)
            await self._handle_success()
            return result

        except Exception as e:
            await self._handle_failure(e)
            raise

    async def _check_state_transition(self):
        """
        Check and update circuit state based on current conditions.
        
        State transition logic:
        OPEN -> HALF_OPEN: After timeout period
        HALF_OPEN -> CLOSED: After success threshold met
        HALF_OPEN -> OPEN: On any failure
        CLOSED -> OPEN: On error threshold exceeded
        
        NOTE: All transitions are logged in metrics if enabled
        """
        now = datetime.utcnow()

        if self._state == CircuitState.OPEN:
            if self._should_transition_to_half_open(now):
                await self._transition_to_half_open()

        elif self._state == CircuitState.HALF_OPEN:
            if self._success_count >= self.config.success_threshold:
                await self._transition_to_closed()
            elif self._failure_count > 0:
                await self._transition_to_open()

        elif self._state == CircuitState.CLOSED:
            if self._should_transition_to_open():
                await self._transition_to_open()

    def _should_transition_to_half_open(self, now: datetime) -> bool:
        """
        Determine if circuit should attempt recovery.
        
        Uses exponential backoff to prevent rapid oscillation:
        timeout * (cooldown_factor ^ consecutive_timeouts)
        
        NOTE: Backoff capped by float precision limits
        """
        if not self._last_failure_time:
            return False

        timeout = self.config.timeout * (
            self.config.cooldown_factor ** self._consecutive_timeouts
        )
        return (now - self._last_failure_time) >= timedelta(seconds=timeout)

    def _should_transition_to_open(self) -> bool:
        """
        Check if circuit should open based on error conditions.
        
        Triggers on either:
        - Absolute failure count threshold
        - Error rate threshold over minimum throughput
        
        NOTE: Requires minimum throughput to prevent premature triggers
        """
        if len(self._request_window) < self.config.min_throughput:
            return False

        if self._failure_count >= self.config.failure_threshold:
            return True

        error_rate = self._calculate_error_rate()
        return error_rate >= self.config.error_rate_threshold

    def _calculate_error_rate(self) -> float:
        """
        Calculate current error rate from rolling window.
        
        Uses fixed-size window to limit memory usage while
        providing meaningful error rate calculation.
        
        NOTE: Returns 0.0 for empty window
        """
        if not self._request_window:
            return 0.0
        return 1 - (sum(self._request_window) / len(self._request_window))

    async def _transition_to_open(self):
        """Transition circuit to open state"""
        self._state = CircuitState.OPEN
        self._last_failure_time = datetime.utcnow()
        self._consecutive_timeouts += 1
        
        if self.metrics:
            await self.metrics.increment(
                "circuit_breaker.state_change",
                tags={"state": "open", "timeouts": self._consecutive_timeouts}
            )

    async def _transition_to_half_open(self):
        """Transition circuit to half-open state"""
        self._state = CircuitState.HALF_OPEN
        self._failure_count = 0
        self._success_count = 0
        
        if self.metrics:
            await self.metrics.increment(
                "circuit_breaker.state_change",
                tags={"state": "half_open"}
            )

    async def _transition_to_closed(self):
        """Transition circuit to closed state"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._consecutive_timeouts = 0
        self._request_window.clear()
        
        if self.metrics:
            await self.metrics.increment(
                "circuit_breaker.state_change",
                tags={"state": "closed"}
            )

    async def _handle_success(self):
        """Handle successful operation"""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
            
            self._update_window(True)
            
            if self.metrics:
                await self.metrics.increment(
                    "circuit_breaker.request",
                    tags={
                        "result": "success",
                        "state": self._state.value
                    }
                )

    async def _handle_failure(self, error: Exception):
        """Handle failed operation"""
        async with self._lock:
            self._failure_count += 1
            self._update_window(False)
            
            if self.metrics:
                await self.metrics.increment(
                    "circuit_breaker.request",
                    tags={
                        "result": "failure",
                        "error": error.__class__.__name__,
                        "state": self._state.value
                    }
                )

    def _update_window(self, success: bool):
        """Update rolling window of results"""
        self._request_window.append(success)
        if len(self._request_window) > self.config.window_size:
            self._request_window.pop(0)

    def _get_remaining_timeout(self) -> float:
        """Get remaining timeout before next retry attempt"""
        if not self._last_failure_time:
            return 0.0

        timeout = self.config.timeout * (
            self.config.cooldown_factor ** self._consecutive_timeouts
        )
        elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
        return max(0.0, timeout - elapsed)

    async def get_state(self) -> Dict[str, Any]:
        """
        Get current circuit breaker state and metrics.
        
        Provides insights into:
        - Current state and transition timing
        - Error rates and thresholds
        - Window statistics
        
        Used for monitoring and debugging circuit behavior.
        """
        async with self._lock:
            return {
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "error_rate": self._calculate_error_rate(),
                "consecutive_timeouts": self._consecutive_timeouts,
                "remaining_timeout": self._get_remaining_timeout(),
                "window_size": len(self._request_window)
            }

class CircuitOpenError(Exception):
    """Error when circuit is open"""
    pass