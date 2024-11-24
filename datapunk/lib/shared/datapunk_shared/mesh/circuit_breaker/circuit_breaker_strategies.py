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
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreakerStrategy:
    """Base strategy for circuit breaker behavior."""
    
    def __init__(self, metrics: 'MetricsClient'):
        self.metrics = metrics
        self.logger = logger.bind(strategy=self.__class__.__name__)
    
    async def should_open(self, failure_count: int, error_rate: float) -> bool:
        """Determine if circuit should open."""
        raise NotImplementedError
    
    async def should_close(self, success_count: int) -> bool:
        """Determine if circuit should close."""
        raise NotImplementedError 