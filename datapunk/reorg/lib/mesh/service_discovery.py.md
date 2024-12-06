## Purpose

The `service_discovery.py` module implements service discovery and registration functionality with Consul integration, providing robust service management and health monitoring capabilities.

## Implementation

- **Core Classes**:

  1. `ServiceRegistration` (lines 24-40)

     - Data class for service registration configuration
     - Defines health check parameters and metadata

  2. `ServiceDiscovery` (lines 42-267)
     - Manages service registration and discovery
     - Implements health monitoring and caching
     - Provides real-time service updates

### Key Components

1. **Service Registration** (lines 76-139):

   - Handles Consul registration with health checks
   - Configures load balancer integration
   - Implements metric collection
   - Provides error handling and logging

2. **Service Discovery** (lines 187-226):

   - Discovers service instances using Consul
   - Implements caching for performance
   - Handles health status filtering
   - Provides metric tracking

3. **Service Watching** (lines 174-267):
   - Implements real-time service monitoring
   - Handles health status changes
   - Updates load balancer configuration
   - Provides error recovery

## Location

Located in `datapunk/lib/mesh/service_discovery.py`, providing core service discovery functionality.

## Integration

- Integrates with:
  - Consul for service registry
  - Health checker for monitoring
  - Load balancer for distribution
  - Metrics system for monitoring
  - Cache system for performance

## Dependencies

- External:

  - `consul`: For service registry operations
  - `structlog`: For structured logging
  - `asyncio`: For async operations
  - `dataclasses`: For data structures

- Internal:
  - `.health.health_checks`: For health monitoring
  - `.load_balancer.load_balancer`: For request distribution
  - `.discovery_metrics`: For performance tracking

## Known Issues

1. Edge cases where Consul registration partially succeeds (FIXME in line 87)
2. DNS caching may affect update speed (WARNING in line 57)
3. May miss rapid changes between polls (WARNING in line 187)

## Refactoring Notes

1. Add support for additional service registries
2. Implement DNS NOTIFY support for faster updates
3. Add DNS-SD service type support
4. Optimize cache invalidation strategy
5. Implement circuit breaker for Consul failures
6. Add support for custom health check endpoints
