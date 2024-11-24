from typing import Dict, Optional, TYPE_CHECKING
import structlog
from datetime import datetime

from datapunk_shared.exceptions import CircuitBreakerError
from .circuit_breaker_strategies import CircuitBreakerStrategy
from .circuit_breaker import CircuitBreaker

if TYPE_CHECKING:
    from datapunk_shared.monitoring import MetricsClient
    from datapunk_shared.cache import CacheClient

logger = structlog.get_logger() 