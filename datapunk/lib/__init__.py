"""
Datapunk Shared Service Library

Core library providing shared functionality across the Datapunk service mesh.
Implements critical infrastructure components for service reliability,
security, and monitoring.

Key components:
- BaseServiceConfig: Service configuration management
- HealthCheck: Service health monitoring
- MetricsCollector: Telemetry and metrics
- CacheManager: Distributed caching
- ServiceMesh: Service discovery and communication

Integration points:
- Metrics pipeline
- Distributed tracing
- Service mesh topology
- Security infrastructure

NOTE: This library is a critical dependency for all Datapunk services.
Version changes should be carefully coordinated across the mesh.

TODO: Add automatic version compatibility checking
TODO: Implement graceful version migration support
FIXME: Add comprehensive component dependency tracking
"""

from .datapunk_shared.config import BaseServiceConfig
from .datapunk_shared.health import HealthCheck
from .metrics import MetricsCollector
from .datapunk_shared.cache import CacheManager
from .mesh import ServiceMesh

# Version tracking for compatibility checks
__version__ = "0.1.0"

# Expose core components for service integration
__all__ = [
    "BaseServiceConfig",  # Service configuration
    "HealthCheck",        # Health monitoring
    "MetricsCollector",   # Telemetry
    "CacheManager",       # Caching
    "ServiceMesh"         # Service communication
] 