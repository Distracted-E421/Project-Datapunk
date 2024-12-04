"""
Service mesh core functionality with circuit breaking and health monitoring.

This module provides:
- Fault tolerance through circuit breakers
- Health monitoring and load balancing
- Service mesh orchestration
- Service integration patterns

Architecture follows the sidecar pattern with:
- Per-service circuit breakers
- Health-aware load balancing
- Centralized monitoring integration
- Distributed caching support

NOTE: Import order matters for proper initialization
"""

from typing import TYPE_CHECKING

# Circuit breaker components for fault tolerance
# Provides cascading failure protection with configurable strategies
from .circuit_breaker.circuit_breaker import CircuitBreaker
from .circuit_breaker.circuit_breaker_manager import CircuitBreakerManager
from .circuit_breaker.circuit_breaker_strategies import CircuitBreakerStrategy
from .circuit_breaker.circuit_breaker_advanced import AdvancedCircuitBreaker

# Health monitoring components for adaptive routing
# Enables intelligent load balancing based on service health
from .health.health_aggregator import HealthAggregator
from .health.health_aware_balancer import HealthAwareLoadBalancer

# Core service mesh components for orchestration
# Handles service discovery, routing, and integration
from .mesh import ServiceMesh
from .integrator import ServiceIntegrator

# Type checking imports for development
# NOTE: These imports are only used during static type checking
if TYPE_CHECKING:
    from ..monitoring import MetricsClient  # For performance monitoring
    from ..cache import CacheClient  # For distributed caching