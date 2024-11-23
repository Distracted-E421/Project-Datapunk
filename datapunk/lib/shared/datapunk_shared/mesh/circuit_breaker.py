from typing import Dict, Any, Optional, Callable, Awaitable
import asyncio
from datetime import datetime, timedelta
import structlog
from prometheus_client import Counter, Gauge
from ..utils.retry import RetryConfig

logger = structlog.get_logger(__name__)

class CircuitBreakerState:
    """Circuit breaker state machine"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: float = 0.5,
        reset_timeout: float = 30.0,
        half_open_max_calls: int = 5,
        window_size: int = 100
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        self.window_size = window_size
        
        # State
        self.state = CircuitBreakerState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        
        # Metrics
        self.state_gauge = Gauge(
            f'circuit_breaker_state_{name}',
            'Circuit breaker state (0=closed, 1=half-open, 2=open)',
            ['service']
        )
        self.failure_counter = Counter(
            f'circuit_breaker_failures_{name}',
            'Number of failures',
            ['service']
        )
        self.success_counter = Counter(
            f'circuit_breaker_successes_{name}',
            'Number of successes',
            ['service']
        )
        
        self._update_metrics()
    
    def _update_metrics(self):
        """Update Prometheus metrics"""
        state_value = {
            CircuitBreakerState.CLOSED: 0,
            CircuitBreakerState.HALF_OPEN: 1,
            CircuitBreakerState.OPEN: 2
        }[self.state]
        
        self.state_gauge.labels(service=self.name).set(state_value)
    
    def _should_trip(self) -> bool:
        """Check if circuit breaker should trip"""
        if self.failures + self.successes < self.window_size:
            return False
            
        failure_rate = self.failures / (self.failures + self.successes)
        return failure_rate >= self.failure_threshold
    
    def _should_reset(self) -> bool:
        """Check if circuit breaker should reset"""
        if not self.last_failure_time:
            return True
            
        elapsed = datetime.utcnow() - self.last_failure_time
        return elapsed >= timedelta(seconds=self.reset_timeout)
    
    async def call(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Execute function with circuit breaker logic"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_reset():
                logger.info(f"Circuit {self.name} entering half-open state")
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                self._update_metrics()
            else:
                raise CircuitBreakerError(f"Circuit {self.name} is open")
                
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                logger.info(f"Circuit {self.name} remaining open")
                self.state = CircuitBreakerState.OPEN
                self._update_metrics()
                raise CircuitBreakerError(f"Circuit {self.name} is open")
                
            self.half_open_calls += 1
            
        try:
            result = await func(*args, **kwargs)
            
            self.successes += 1
            self.success_counter.labels(service=self.name).inc()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                logger.info(f"Circuit {self.name} closing")
                self.state = CircuitBreakerState.CLOSED
                self.failures = 0
                self.successes = 0
                self._update_metrics()
                
            return result
            
        except Exception as e:
            self.failures += 1
            self.failure_counter.labels(service=self.name).inc()
            self.last_failure_time = datetime.utcnow()
            
            if self._should_trip():
                logger.warning(f"Circuit {self.name} tripping")
                self.state = CircuitBreakerState.OPEN
                self._update_metrics()
                
            raise CircuitBreakerError(f"Circuit {self.name} call failed") from e

class CircuitBreakerError(Exception):
    """Raised when circuit breaker prevents operation"""
    pass

class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        
    def get_or_create(
        self,
        name: str,
        **kwargs: Any
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one"""
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(name, **kwargs)
        return self.breakers[name]
    
    def get_all_states(self) -> Dict[str, str]:
        """Get states of all circuit breakers"""
        return {
            name: breaker.state
            for name, breaker in self.breakers.items()
        }
    
    async def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.state = CircuitBreakerState.CLOSED
            breaker.failures = 0
            breaker.successes = 0
            breaker.last_failure_time = None
            breaker.half_open_calls = 0
            breaker._update_metrics() 