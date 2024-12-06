## Purpose

The `discovery.py` module implements service discovery with caching and health monitoring capabilities, providing robust service instance management and real-time health status tracking through Consul integration.

## Implementation

- **Core Classes**:

  1. `ServiceEndpoint` (lines 29-46)

     - Represents service instance details
     - Tracks health status and metadata
     - Manages instance identity

  2. `ServiceDiscoveryConfig` (lines 47-65)

     - Configures discovery behavior
     - Manages cache and health check settings
     - Controls deregistration timeouts

  3. `ServiceDiscoveryManager` (lines 66-324)
     - Implements discovery operations
     - Manages service lifecycle
     - Handles health monitoring

### Key Components

1. **Service Registration** (lines 98-151):

   - Consul registration with health checks
   - Unique service ID generation
   - Metric collection
   - Error handling

2. **Service Discovery** (lines 154-210):

   - Cache-first lookup strategy
   - Health status filtering
   - Metric tracking
   - Error recovery

3. **Service Watching** (lines 212-262):

   - Real-time service monitoring
   - Long polling implementation
   - Cache updates
   - Error backoff

4. **Cache Management** (lines 263-324):
   - Efficient lookup caching
   - TTL-based invalidation
   - Error handling
   - Metric collection

## Location

Located in `datapunk/lib/mesh/discovery.py`, providing core service discovery functionality.

## Integration

- Integrates with:
  - Consul for service registry
  - Cache client for performance
  - Metrics for monitoring
  - Tracing for observability
  - Health checks for monitoring

## Dependencies

- External:

  - `consul`: For service registry
  - `structlog`: For logging
  - `aiohttp`: For HTTP operations
  - `asyncio`: For async support
  - `dataclasses`: For data structures

- Internal:
  - `.metrics`: For performance tracking
  - `..cache`: For caching operations
  - `..tracing`: For distributed tracing
  - `..exceptions`: For error handling

## Known Issues

1. May miss updates during reconnection (WARNING in line 225)
2. Handle cases where no instances are available (FIXME in line 202)
3. Cache may briefly serve stale data (implied by caching strategy)

## Refactoring Notes

1. Implement circuit breaker for Consul failures
2. Add support for custom health check endpoints
3. Optimize cache invalidation strategy
4. Add support for service dependencies
5. Implement retry budget mechanism
6. Add support for service versioning
