"""
Advanced Service Mesh Circuit Breaker

Implements an enhanced circuit breaker pattern for the Datapunk service mesh
with distributed state management and adaptive failure detection. Provides
robust service protection with minimal false positives.

Key features:
- Distributed state management
- Adaptive failure thresholds
- Half-open state testing
- Metric integration
- Cache-based state sharing

See sys-arch.mmd Reliability/CircuitBreaker for implementation details.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
import structlog
from datetime import datetime, timedelta

from .circuit_breaker import CircuitBreaker
from .circuit_breaker_strategies import CircuitState, GradualRecoveryStrategy
from datapunk_shared.exceptions import CircuitBreakerError

if TYPE_CHECKING:
    from datapunk_shared.monitoring import MetricsClient
    from datapunk_shared.cache import CacheClient

logger = structlog.get_logger()

class AdvancedCircuitBreaker(CircuitBreaker):
    """
    Enhanced circuit breaker with distributed state management.
    
    Extends basic circuit breaker with cache-based state sharing
    and advanced failure detection. Designed for high-availability
    environments with multiple service instances.
    
    TODO: Add support for custom failure detection strategies
    TODO: Implement circuit state prediction
    """
    
    def __init__(self,
                 service_name: str,
                 metrics: 'MetricsClient',
                 cache: 'CacheClient',
                 failure_threshold: int = 5,
                 recovery_timeout: int = 30,
                 half_open_timeout: int = 5,
                 strategy: Optional['CircuitBreakerStrategy'] = None):
        """
        Initialize advanced circuit breaker.
        
        Parameters are tuned for typical microservice behavior:
        - failure_threshold: Trips after 5 failures
        - recovery_timeout: 30s cool-down period
        - half_open_timeout: 5s test window
        
        Args:
            strategy: Custom circuit breaker strategy (defaults to GradualRecoveryStrategy)
        
        NOTE: These values should be adjusted based on specific
        service characteristics and SLAs.
        """
        super().__init__(service_name, metrics)
        self.cache = cache
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_timeout = half_open_timeout
        self.logger = logger.bind(component="advanced_circuit_breaker")
        
        # Initialize with gradual recovery by default
        self.strategy = strategy or GradualRecoveryStrategy(
            metrics=metrics,
            base_recovery_rate=0.1,  # Start with 10% traffic
            recovery_step=0.1,       # Increase by 10% per window
            error_threshold=0.1      # Max 10% errors during recovery
        )
        
    async def allow_request(self) -> bool:
        """
        Check if request should be allowed through circuit.
        
        Implements:
        1. Basic circuit state checks
        2. Gradual recovery rate limiting
        3. Distributed state management
        4. Metric collection
        
        Returns:
            bool: True if request should be allowed
        """
        # Get current state from cache
        state = await self._get_cached_state()
        
        if state == CircuitState.OPEN:
            await self.metrics.increment(
                "circuit_breaker_rejections",
                {"service": self.service_name}
            )
            return False
            
        if state == CircuitState.HALF_OPEN:
            # Use strategy to determine request allowance
            allowed_rate = await self.strategy.get_allowed_request_rate()
            
            # Randomly allow requests based on rate
            import random
            if random.random() > allowed_rate:
                await self.metrics.increment(
                    "circuit_breaker_recovery_rejections",
                    {"service": self.service_name}
                )
                return False
                
        return True
        
    async def record_success(self):
        """Record successful request and update recovery state."""
        await super().record_success()
        
        if self.state == CircuitState.HALF_OPEN:
            if await self.strategy.should_close(self.success_count):
                await self._transition_state(CircuitState.CLOSED)
                await self.strategy.reset_recovery()
                
    async def record_failure(self):
        """Record failed request and check for circuit opening."""
        await super().record_failure()
        
        # Check if circuit should open
        if await self.strategy.should_open(
            self.failure_count,
            await self._calculate_error_rate()
        ):
            await self._transition_state(CircuitState.OPEN)
            await self.strategy.reset_recovery()
            
    async def _calculate_error_rate(self) -> float:
        """Calculate current error rate for strategy decisions."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.failure_count / total
        
    async def _get_cached_state(self) -> CircuitState:
        """Get circuit state from distributed cache."""
        try:
            state = await self.cache.get(
                f"circuit:{self.service_name}:state"
            )
            return CircuitState(state) if state else CircuitState.CLOSED
        except Exception as e:
            self.logger.error("Failed to get circuit state", error=str(e))
            return self.state  # Fallback to local state
            
    async def _transition_state(self, new_state: CircuitState):
        """Update circuit state in both cache and local memory."""
        self.state = new_state
        try:
            await self.cache.set(
                f"circuit:{self.service_name}:state",
                new_state.value,
                expire=self.recovery_timeout * 2
            )
        except Exception as e:
            self.logger.error("Failed to update circuit state", error=str(e))
            
    async def _check_recovery_timeout(self) -> bool:
        """Check if enough time has passed for recovery attempt."""
        try:
            last_failure = await self.cache.get(
                f"circuit:{self.service_name}:last_failure"
            )
            if not last_failure:
                return True
                
            elapsed = datetime.utcnow() - datetime.fromisoformat(last_failure)
            return elapsed.total_seconds() >= self.recovery_timeout
            
        except Exception as e:
            self.logger.error("Failed to check recovery timeout", error=str(e))
            return True  # Fail open on cache errors