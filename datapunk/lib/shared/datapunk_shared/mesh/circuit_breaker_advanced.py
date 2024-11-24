from typing import Optional, Dict, Any, Callable
import asyncio
import time
import structlog
from enum import Enum
from dataclasses import dataclass
from .health_trend_analyzer import HealthTrendAnalyzer, TrendDirection
from .metrics import CircuitBreakerMetrics

logger = structlog.get_logger()

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5           # Failures before opening
    success_threshold: int = 3           # Successes needed to close
    reset_timeout: float = 60.0          # Seconds before half-open
    half_open_timeout: float = 30.0      # Seconds in half-open before decision
    window_size: int = 60                # Rolling window size in seconds
    error_rate_threshold: float = 0.5    # Error rate to trigger opening
    min_throughput: int = 10             # Min requests before error rate check

class CircuitBreakerMetadata:
    """Metadata for circuit breaker state."""
    def __init__(self):
        self.failures = 0
        self.successes = 0
        self.last_failure_time = 0.0
        self.last_state_change = time.time()
        self.error_timestamps: List[float] = []
        self.request_timestamps: List[float] = []

class AdvancedCircuitBreaker:
    """Advanced circuit breaker with health trend analysis."""
    
    def __init__(self,
                 service: str,
                 config: CircuitBreakerConfig,
                 health_analyzer: HealthTrendAnalyzer,
                 metrics: CircuitBreakerMetrics):
        self.service = service
        self.config = config
        self.health_analyzer = health_analyzer
        self.metrics = metrics
        self.state = CircuitState.CLOSED
        self.metadata = CircuitBreakerMetadata()
        self.logger = logger.bind(service=service, component="circuit_breaker")
    
    async def execute(self,
                     operation: Callable,
                     fallback: Optional[Callable] = None,
                     **kwargs) -> Any:
        """Execute operation with circuit breaker protection."""
        if not await self.can_execute():
            self.metrics.record_rejection(self.service)
            if fallback:
                return await fallback(**kwargs)
            raise CircuitOpenError(f"Circuit breaker open for {self.service}")
        
        start_time = time.time()
        try:
            result = await operation(**kwargs)
            await self.record_success()
            
            # Record metrics
            duration = time.time() - start_time
            self.metrics.record_success(self.service, duration)
            
            return result
            
        except Exception as e:
            await self.record_failure()
            
            # Record metrics
            duration = time.time() - start_time
            self.metrics.record_failure(self.service, str(e), duration)
            
            raise
    
    async def can_execute(self) -> bool:
        """Check if operation can be executed."""
        current_time = time.time()
        
        if self.state == CircuitState.OPEN:
            if current_time - self.metadata.last_state_change >= self.config.reset_timeout:
                await self._transition_to_half_open()
                return True
            return False
            
        if self.state == CircuitState.HALF_OPEN:
            if self.metadata.successes >= self.config.success_threshold:
                await self._transition_to_closed()
                return True
            if current_time - self.metadata.last_state_change >= self.config.half_open_timeout:
                await self._transition_to_open()
                return False
            return True
            
        return True
    
    async def record_success(self):
        """Record successful operation."""
        self.metadata.successes += 1
        self.metadata.request_timestamps.append(time.time())
        
        # Trim old timestamps
        self._trim_timestamps()
        
        # Check for state transition in half-open
        if self.state == CircuitState.HALF_OPEN:
            if self.metadata.successes >= self.config.success_threshold:
                await self._transition_to_closed()
    
    async def record_failure(self):
        """Record failed operation."""
        current_time = time.time()
        self.metadata.failures += 1
        self.metadata.last_failure_time = current_time
        self.metadata.error_timestamps.append(current_time)
        self.metadata.request_timestamps.append(current_time)
        
        # Trim old timestamps
        self._trim_timestamps()
        
        # Check error rate and health trend
        if await self._should_open():
            await self._transition_to_open()
    
    async def _should_open(self) -> bool:
        """Determine if circuit should open based on multiple factors."""
        # Check basic failure threshold
        if self.metadata.failures >= self.config.failure_threshold:
            return True
        
        # Check error rate if enough requests
        if len(self.metadata.request_timestamps) >= self.config.min_throughput:
            error_rate = len(self.metadata.error_timestamps) / len(self.metadata.request_timestamps)
            if error_rate >= self.config.error_rate_threshold:
                return True
        
        # Check health trend
        trend = await self.health_analyzer.analyze_trend(self.service, "circuit_breaker")
        if trend.direction == TrendDirection.DEGRADING and trend.confidence > 0.8:
            return True
        
        return False
    
    async def _transition_to_open(self):
        """Transition to open state."""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            self.metadata.last_state_change = time.time()
            self.logger.warning("circuit_opened",
                              failures=self.metadata.failures,
                              error_rate=self._calculate_error_rate())
            self.metrics.record_state_change(self.service, "open")
    
    async def _transition_to_half_open(self):
        """Transition to half-open state."""
        self.state = CircuitState.HALF_OPEN
        self.metadata.last_state_change = time.time()
        self.metadata.successes = 0
        self.logger.info("circuit_half_open")
        self.metrics.record_state_change(self.service, "half_open")
    
    async def _transition_to_closed(self):
        """Transition to closed state."""
        self.state = CircuitState.CLOSED
        self.metadata.last_state_change = time.time()
        self.metadata.failures = 0
        self.metadata.successes = 0
        self.logger.info("circuit_closed")
        self.metrics.record_state_change(self.service, "closed")
    
    def _trim_timestamps(self):
        """Trim timestamps outside window."""
        cutoff = time.time() - self.config.window_size
        self.metadata.error_timestamps = [
            ts for ts in self.metadata.error_timestamps
            if ts > cutoff
        ]
        self.metadata.request_timestamps = [
            ts for ts in self.metadata.request_timestamps
            if ts > cutoff
        ]
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate."""
        if not self.metadata.request_timestamps:
            return 0.0
        return len(self.metadata.error_timestamps) / len(self.metadata.request_timestamps)

class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass 