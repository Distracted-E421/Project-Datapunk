# DNS Resolver Component

## Purpose

Provides enhanced DNS-based service discovery with caching and failover support for the Datapunk service mesh.

## Context

The DNS resolver is a critical component in the service discovery system, enabling services to locate and connect to other services using DNS infrastructure. It integrates with the mesh's caching and health monitoring systems.

## Dependencies

- dns.resolver
- dns.asyncresolver
- structlog
- CacheClient (internal)
- ServiceRegistration (internal)
- ServiceMetadata (internal)
- ServiceDiscoveryError (internal)

## Core Components

### DNSResolverConfig

Configuration dataclass for DNS resolver settings:

- Multiple DNS server support
- Configurable timeouts
- Cache TTL management
- Failover retry settings
- IPv4/IPv6 preferences

### DNSServiceResolver

Main resolver class implementing:

- DNS-based service discovery
- Multi-level caching (local and distributed)
- Automatic failover handling
- Health monitoring
- IPv4/IPv6 support

## Key Features

### Caching Strategy

- Two-tier caching system:
  - Local in-memory cache
  - Distributed cache via CacheClient
- Configurable TTL for cache entries
- Cache invalidation on health status changes

### DNS Resolution Process

1. Check local cache
2. Check distributed cache
3. Perform DNS lookup
4. Update caches
5. Apply metadata filters

### Failover Handling

- Configurable retry attempts
- Automatic failover to backup servers
- Exponential backoff for retries
- Health status monitoring

### Address Resolution

- Dual-stack IPv4/IPv6 support
- Configurable IP version preferences
- Fallback mechanisms for unavailable protocols

## Performance Considerations

- Cache hit rates significantly impact resolution speed
- DNS timeout settings affect latency under failure
- Memory usage scales with cached service count
- Network overhead from health checks and cache updates

## Security Considerations

- DNS response validation
- Cache poisoning prevention
- Timeout and retry limits
- Health check endpoint security

## Known Issues

- Memory usage may grow with large service counts
- Cache coherency challenges in distributed setups
- Potential DNS resolution bias in multi-zone deployments

## Trade-offs and Design Decisions

1. Cache vs Consistency

   - Uses TTL-based caching for performance
   - Accepts potential stale data within TTL window
   - Provides configuration knobs for tuning

2. IPv4 vs IPv6

   - Supports both protocols with preferences
   - Default IPv4 preference for compatibility
   - Configurable fallback behavior

3. Local vs Distributed Cache
   - Two-tier approach balances speed and consistency
   - Local cache reduces network overhead
   - Distributed cache ensures mesh-wide visibility
