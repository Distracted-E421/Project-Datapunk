from typing import TYPE_CHECKING

# Circuit breaker components
from .circuit_breaker.circuit_breaker import CircuitBreaker
from .circuit_breaker.circuit_breaker_manager import CircuitBreakerManager
from .circuit_breaker.circuit_breaker_strategies import CircuitBreakerStrategy
from .circuit_breaker.circuit_breaker_advanced import AdvancedCircuitBreaker

# Health check components
from .health.health_aggregator import HealthAggregator
from .health.health_aware_balancer import HealthAwareLoadBalancer

# Core mesh components
from .mesh import ServiceMesh
from .integrator import ServiceIntegrator

if TYPE_CHECKING:
    from ..monitoring import MetricsClient
    from ..cache import CacheClient 