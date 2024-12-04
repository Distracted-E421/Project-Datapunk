# Service Discovery Implementation (discovery.py)

## Purpose

Implements core service discovery functionality with caching, health monitoring, and real-time service tracking capabilities.

## Context

Critical component of the service mesh that manages service registration, discovery, and health monitoring through integration with Consul and custom caching mechanisms.

## Dependencies

- structlog: For structured logging
- consul: For service registry
- aiohttp: For async HTTP operations
- Cache client: For response optimization
- Metrics: For performance monitoring
- Tracing: For distributed tracing

## Core Components

### ServiceEndpoint Class

```python
@dataclass
class ServiceEndpoint:
    id: str
    address: str
    port: int
    healthy: bool = True
    last_check: Optional[datetime] = None
    metadata: Dict[str, str] = None
```

Represents service instance with:

- Instance identity
- Network location
- Health status
- Monitoring data

### ServiceDiscoveryConfig Class

```python
@dataclass
class ServiceDiscoveryConfig:
    consul_host: str = "consul"
    consul_port: int = 8500
    cache_ttl: int = 30
    health_check_interval: int = 10
    deregister_critical_timeout: str = "1m"
    enable_caching: bool = True
```

Configuration for:

- Consul connection
- Cache behavior
- Health checks
- Instance lifecycle

### ServiceDiscoveryManager Class

Primary implementation providing:

- Service registration
- Instance discovery
- Health monitoring
- Cache management
- Real-time updates

## Implementation Details

### Service Registration

```python
@trace_method("register_service")
async def register_service(self,
                         service_name: str,
                         host: str,
                         port: int,
                         tags: List[str] = None,
                         metadata: Dict[str, str] = None) -> str:
```

- Creates unique service ID
- Configures health checks
- Registers with Consul
- Updates metrics
- Handles failures

### Service Discovery

```python
@trace_method("discover_service")
async def discover_service(self,
                         service_name: str,
                         use_cache: bool = True) -> List[ServiceEndpoint]:
```

- Cache-first lookups
- Health status filtering
- Metric collection
- Error handling

### Service Watching

```python
@trace_method("watch_service")
async def watch_service(self,
                      service_name: str,
                      callback: callable) -> None:
```

- Real-time updates
- Long polling
- Automatic reconnection
- Error recovery

## Performance Considerations

- Cache utilization impact
- Health check frequency
- Watch operation overhead
- Registration scaling
- Query patterns

## Security Considerations

- Consul communication
- Health check endpoints
- Cache security
- Metadata protection
- Access control

## Known Issues

- Cache consistency
- Watch reconnection
- Health check timing
- Registration races
- Query timeouts

## Trade-offs and Design Decisions

### Caching Strategy

- **Decision**: TTL-based caching
- **Rationale**: Balance freshness and performance
- **Trade-off**: Consistency vs. speed

### Health Monitoring

- **Decision**: HTTP-based health checks
- **Rationale**: Standard and reliable
- **Trade-off**: Simplicity vs. flexibility

### Watch Implementation

- **Decision**: Long polling with backoff
- **Rationale**: Reliable update detection
- **Trade-off**: Resource usage vs. latency

## Future Improvements

1. Enhanced cache invalidation
2. Custom health check protocols
3. Watch operation optimizations
4. Advanced failure detection
5. Extended metadata support

## Example Usage

```python
# Initialize manager
manager = ServiceDiscoveryManager(
    ServiceDiscoveryConfig(
        consul_host="consul.local",
        cache_ttl=60
    )
)

# Register service
service_id = await manager.register_service(
    "api_service",
    "api.local",
    8080,
    tags=["v1"],
    metadata={"version": "1.0.0"}
)

# Discover services
endpoints = await manager.discover_service("api_service")

# Watch for changes
async def on_change(endpoints):
    print(f"Service updated: {len(endpoints)} instances")

await manager.watch_service("api_service", on_change)
```

## Related Components

- Service Registry
- Health Monitor
- Cache Manager
- Metrics Collector
- Load Balancer

## Testing Considerations

1. Registration flows
2. Discovery scenarios
3. Cache behavior
4. Watch operations
5. Error handling
6. Scale testing
7. Network failures

## Monitoring and Observability

- Registration success rate
- Discovery latency
- Cache hit ratio
- Watch operation health
- Error patterns
- Instance health status

## Deployment Considerations

1. Consul cluster setup
2. Network configuration
3. Cache infrastructure
4. Monitoring integration
5. Security policies

## Error Handling

- Registration failures
- Discovery timeouts
- Cache errors
- Watch interruptions
- Network issues
- Health check failures

## Caching Implementation

```python
async def _get_cached_service(self,
                            service_name: str) -> Optional[List[ServiceEndpoint]]:
```

Features:

- Fast lookup path
- Metric tracking
- Error handling
- Serialization
- TTL management

## Health Check Integration

```python
"Check": {
    "HTTP": f"http://{host}:{port}/health",
    "Method": "GET",
    "Interval": f"{self.config.health_check_interval}s",
    "Timeout": "5s",
    "DeregisterCriticalServiceAfter": self.config.deregister_critical_timeout
}
```

Provides:

- HTTP health checks
- Configurable intervals
- Automatic deregistration
- Timeout handling
- Status tracking
