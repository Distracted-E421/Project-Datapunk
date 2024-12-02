"""
Service Mesh Circuit Breaker Strategies

Implements configurable failure detection and recovery strategies for
the Datapunk service mesh circuit breaker system. Provides flexible
reliability patterns adaptable to different service characteristics.

Key features:
- Configurable failure detection
- Adaptive recovery patterns
- State transition management
- Performance impact control
- Metric integration

See sys-arch.mmd Reliability/CircuitBreakerStrategies for implementation details.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from enum import Enum
import structlog
from datetime import datetime, timedelta

from datapunk_shared.exceptions import CircuitBreakerError
from datapunk_shared.monitoring.metrics import MetricType

if TYPE_CHECKING:
    from datapunk_shared.monitoring import MetricsClient

logger = structlog.get_logger()

class CircuitState(Enum):
    """
    Circuit breaker state machine definition.
    
    Implements three-state reliability pattern for graceful
    failure handling and recovery:
    """
    CLOSED = "closed"      # Normal operation, requests flow freely
    OPEN = "open"         # Failure detected, requests blocked
    HALF_OPEN = "half_open"  # Testing recovery, limited requests

class CircuitBreakerStrategy:
    """
    Base strategy for circuit breaker behavior.
    
    Defines interface for customizable failure detection and
    recovery patterns. Strategies can be swapped at runtime
    to adapt to changing service behavior.
    
    TODO: Add support for ML-based failure prediction
    TODO: Implement gradual recovery patterns
    
    NOTE: Implementations should minimize computational overhead
    to prevent impact on request processing.
    """
    
    def __init__(self, metrics: 'MetricsClient'):
        """
        Initialize strategy with metric integration.
        
        NOTE: Metrics are required for strategy effectiveness
        monitoring and tuning.
        """
        self.metrics = metrics
        self.logger = logger.bind(strategy=self.__class__.__name__)
    
    async def should_open(self, failure_count: int, error_rate: float) -> bool:
        """
        Determine if circuit should transition to open state.
        
        Evaluates current failure patterns against strategy-specific
        thresholds. Should consider both absolute failures and
        error rates to handle varying traffic volumes.
        """
        raise NotImplementedError
    
    async def should_close(self, success_count: int) -> bool:
        """
        Determine if circuit should return to closed state.
        
        Tests recovery stability during half-open state to prevent
        premature recovery that could trigger failure cascades.
        """
        raise NotImplementedError

class GradualRecoveryStrategy(CircuitBreakerStrategy):
    """
    Implements gradual recovery pattern for circuit breaker.
    
    Features:
    - Progressive request rate increase
    - Error rate monitoring during recovery
    - Adaptive recovery speed
    - Metric tracking for recovery effectiveness
    
    Recovery phases:
    1. Initial testing (10% traffic)
    2. Gradual increase (10% -> 50%)
    3. Full recovery (50% -> 100%)
    
    NOTE: Recovery speed adapts based on error rates during recovery
    """
    
    def __init__(self, metrics: 'MetricsClient',
                 base_recovery_rate: float = 0.1,
                 recovery_step: float = 0.1,
                 error_threshold: float = 0.1):
        """
        Initialize gradual recovery strategy.
        
        Args:
            base_recovery_rate: Initial traffic percentage (0.1 = 10%)
            recovery_step: Traffic increase per success window
            error_threshold: Max allowed error rate during recovery
        """
        super().__init__(metrics)
        self.base_recovery_rate = base_recovery_rate
        self.recovery_step = recovery_step
        self.error_threshold = error_threshold
        self.current_recovery_rate = base_recovery_rate
        self._recovery_start_time = None
        
    async def should_open(self, failure_count: int, error_rate: float) -> bool:
        """
        Check if circuit should open based on failures.
        
        Uses both absolute failure count and error rate to make
        decisions, with error rate weighted more heavily during
        recovery to prevent oscillation.
        """
        # Record metrics for monitoring
        await self.metrics.record_gauge(
            "circuit_breaker_error_rate",
            error_rate,
            {"strategy": "gradual_recovery"}
        )
        
        # More sensitive during recovery
        if self._recovery_start_time is not None:
            return error_rate > self.error_threshold
            
        # Normal operation checks
        return failure_count >= 5 or error_rate > 0.2
        
    async def should_close(self, success_count: int) -> bool:
        """
        Determine if circuit should close based on recovery pattern.
        
        Implements gradual recovery by:
        1. Starting with base_recovery_rate traffic
        2. Increasing by recovery_step after each success window
        3. Monitoring error rates during recovery
        4. Adapting recovery speed based on stability
        """
        if success_count < 3:  # Minimum success threshold
            return False
            
        if self._recovery_start_time is None:
            self._recovery_start_time = datetime.utcnow()
            self.current_recovery_rate = self.base_recovery_rate
            
        # Record recovery progress
        await self.metrics.record_gauge(
            "circuit_breaker_recovery_rate",
            self.current_recovery_rate,
            {"strategy": "gradual_recovery"}
        )
        
        # Increase recovery rate after success window
        self.current_recovery_rate = min(
            1.0,  # Cap at 100%
            self.current_recovery_rate + self.recovery_step
        )
        
        # Circuit fully closes at 100% recovery rate
        return self.current_recovery_rate >= 1.0
        
    async def get_allowed_request_rate(self) -> float:
        """
        Get current allowed request percentage during recovery.
        
        Returns:
            float: Percentage of requests to allow (0.0-1.0)
        """
        if self._recovery_start_time is None:
            return 1.0  # Full traffic when not in recovery
            
        return self.current_recovery_rate
        
    async def reset_recovery(self):
        """Reset recovery progress on new failures."""
        self._recovery_start_time = None
        self.current_recovery_rate = self.base_recovery_rate