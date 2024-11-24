from typing import Optional, Dict, Any, TYPE_CHECKING
import structlog
from datetime import datetime, timedelta

from .circuit_breaker import CircuitBreaker
from .circuit_breaker_strategies import CircuitState
from datapunk_shared.exceptions import CircuitBreakerError

if TYPE_CHECKING:
    from datapunk_shared.monitoring import MetricsClient
    from datapunk_shared.cache import CacheClient

logger = structlog.get_logger()

class AdvancedCircuitBreaker(CircuitBreaker):
    """Enhanced circuit breaker with advanced features."""
    
    def __init__(self,
                 service_name: str,
                 metrics: 'MetricsClient',
                 cache: 'CacheClient',
                 failure_threshold: int = 5,
                 recovery_timeout: int = 30,
                 half_open_timeout: int = 5):
        super().__init__(service_name, metrics)
        self.cache = cache
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_timeout = half_open_timeout
        self.logger = logger.bind(component="advanced_circuit_breaker") 