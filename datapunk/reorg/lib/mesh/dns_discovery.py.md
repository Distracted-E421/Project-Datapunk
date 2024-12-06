## Purpose

The `dns_discovery.py` module implements DNS-based service discovery with SRV record support, providing service discovery through DNS infrastructure with support for dual-stack networking and health monitoring.

## Implementation

- **Core Classes**:

  1. `DNSConfig` (lines 26-46)

     - Configures DNS discovery settings
     - Manages timeouts and retries
     - Controls caching behavior

  2. `DNSServiceDiscovery` (lines 47-208)
     - Implements DNS-based discovery
     - Handles SRV record resolution
     - Manages service monitoring

### Key Components

1. **DNS Configuration** (lines 26-46):

   - Domain suffix management
   - DNS server configuration
   - Cache TTL settings
   - Timeout handling

2. **Service Discovery** (lines 73-116):

   - SRV record querying
   - A/AAAA record resolution
   - Endpoint list building
   - Error handling

3. **Address Resolution** (lines 140-172):

   - Dual-stack IPv4/IPv6 support
   - Fallback handling
   - Error recovery
   - Address validation

4. **Service Watching** (lines 174-208):
   - Change detection
   - Polling implementation
   - Callback notifications
   - Error recovery

## Location

Located in `datapunk/lib/mesh/dns_discovery.py`, providing DNS-based service discovery functionality.

## Integration

- Integrates with:
  - DNS infrastructure
  - Service discovery system
  - Health monitoring
  - Change detection
  - Callback system

## Dependencies

- External:

  - `dns.resolver`: For DNS operations
  - `dns.asyncresolver`: For async DNS
  - `structlog`: For logging
  - `asyncio`: For async operations
  - `dataclasses`: For configuration

- Internal:
  - `.discovery`: For service endpoints
  - `..exceptions`: For error handling

## Known Issues

1. DNS caching may affect update speed (WARNING in line 57)
2. May miss rapid changes between polls (WARNING in line 187)
3. Need support for custom record types (TODO in line 38)
4. Need DNS-SD service type support (TODO in line 58)

## Refactoring Notes

1. Add DNS NOTIFY support for faster updates
2. Implement DNS-SD service type support
3. Add support for custom record types
4. Optimize polling intervals
5. Add DNS security extensions support
6. Implement service type discovery
