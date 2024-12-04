# DNS-Based Service Discovery (dns_discovery.py)

## Purpose

Implements DNS-based service discovery with SRV record support, providing dual-stack IPv4/IPv6 resolution, health monitoring, and change detection capabilities.

## Context

Alternative service discovery mechanism that uses DNS infrastructure for service location and health monitoring, particularly useful in environments where Consul is not available.

## Dependencies

- structlog: For structured logging
- dns.resolver: For DNS resolution
- dns.asyncresolver: For async DNS operations
- ServiceEndpoint: For service representation
- ServiceDiscoveryError: For error handling

## Core Components

### DNSConfig Class

```python
@dataclass
class DNSConfig:
    domain_suffix: str = "service.consul"
    dns_port: int = 8600
    dns_servers: List[str] = None
    cache_ttl: int = 30
    timeout: float = 5.0
    max_retries: int = 3
```

Configuration for:

- DNS service naming
- Connection settings
- Performance tuning
- Error handling

### DNSServiceDiscovery Class

Primary implementation providing:

- SRV record resolution
- IPv4/IPv6 support
- Health monitoring
- Change detection
- Service watching

## Implementation Details

### Service Discovery

```python
async def discover_service(self, service_name: str) -> List[ServiceEndpoint]:
```

Process:

1. Query SRV records
2. Resolve A/AAAA records
3. Build endpoint list
4. Track health status

### SRV Record Query

```python
async def _query_srv_records(self, fqdn: str) -> List[Any]:
```

Features:

- Automatic retries
- Timeout handling
- Error logging
- Empty result handling

### Address Resolution

```python
async def _resolve_addresses(self, hostname: str) -> List[str]:
```

Strategy:

- IPv4 resolution
- IPv6 fallback
- Error handling
- Result aggregation

## Performance Considerations

- DNS query caching
- Resolution timeouts
- Retry overhead
- Polling frequency
- Record TTLs

## Security Considerations

- DNS security
- Query validation
- Result verification
- Resource protection
- Access control

## Known Issues

- DNS caching effects
- Resolution delays
- Watch polling gaps
- IPv6 compatibility
- TTL management

## Trade-offs and Design Decisions

### DNS-Based Discovery

- **Decision**: DNS infrastructure usage
- **Rationale**: Universal availability
- **Trade-off**: Simplicity vs. features

### Dual-Stack Support

- **Decision**: IPv4 and IPv6 support
- **Rationale**: Future-proof compatibility
- **Trade-off**: Complexity vs. coverage

### Watch Implementation

- **Decision**: Polling-based watching
- **Rationale**: Simple and reliable
- **Trade-off**: Resource usage vs. latency

## Future Improvements

1. DNS NOTIFY support
2. Custom record types
3. DNSSEC integration
4. Enhanced caching
5. Watch optimizations

## Example Usage

```python
# Initialize discovery
discovery = DNSServiceDiscovery(
    DNSConfig(
        domain_suffix="services.local",
        dns_servers=["10.0.0.1"]
    )
)

# Discover service
endpoints = await discovery.discover_service("api")

# Watch for changes
async def on_change(endpoints):
    print(f"Service updated: {len(endpoints)} instances")

await discovery.watch_service("api", on_change)
```

## Related Components

- Service Discovery
- Health Monitor
- DNS Infrastructure
- Service Registry
- Change Detector

## Testing Considerations

1. DNS resolution
2. IPv6 support
3. Timeout handling
4. Watch behavior
5. Error scenarios
6. Scale testing
7. Network failures

## Monitoring and Observability

- Resolution success
- Query latency
- Error patterns
- Watch operations
- Health status
- Address changes

## Deployment Considerations

1. DNS infrastructure
2. Network setup
3. IPv6 readiness
4. Monitoring integration
5. Security policies

## Error Handling

- Resolution failures
- Timeout errors
- Network issues
- Invalid records
- Watch interruptions

## DNS Integration

```python
# Configure resolver
self.resolver = dns.asyncresolver.Resolver()
if config.dns_servers:
    self.resolver.nameservers = config.dns_servers
self.resolver.port = config.dns_port
self.resolver.timeout = config.timeout
self.resolver.lifetime = config.timeout * config.max_retries
```

Provides:

- Custom nameservers
- Port configuration
- Timeout settings
- Retry behavior
- Error handling

## Service Watching

```python
async def watch_service(self,
                      service_name: str,
                      callback: callable,
                      interval: float = 30.0) -> None:
```

Features:

- Periodic polling
- Change detection
- Error recovery
- State tracking
- Callback notifications

## Resolution Strategy

1. Query SRV records for service
2. Extract target hosts and ports
3. Resolve IPv4 addresses
4. Attempt IPv6 resolution
5. Combine results
6. Create endpoints
7. Track health status

## Health Monitoring

- Instance reachability
- Record validity
- Resolution success
- Address availability
- Service status
