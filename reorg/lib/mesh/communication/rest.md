# REST Communication Module

## Purpose

Provides secure, monitored REST communication capabilities for the Datapunk service mesh, implementing both client and server components with comprehensive security, monitoring, and reliability features.

## Core Components

### RestClient (`client.py`)

#### Primary Features

- Service mesh integration
- Security-first design with mTLS support
- Comprehensive monitoring
- Retry and circuit breaker patterns
- Streaming support
- WebSocket capabilities

#### Key Classes

1. **RestClientConfig**

   - Security configuration (mTLS, tokens)
   - Connection management settings
   - Timeout and retry policies
   - Monitoring configuration

   ```python
   @dataclass
   class RestClientConfig:
       base_url: str
       timeout: float = 30.0
       max_connections: int = 100
       mtls_config: Optional[MTLSConfig] = None
       security_policy: Optional[SecurityPolicy] = None
       retry_policy: Optional[RetryPolicy] = None
       circuit_breaker: Optional[CircuitBreaker] = None
   ```

2. **RestClient**
   - Async REST client implementation
   - Security context management
   - Request tracing and metrics
   - Connection pooling
   - Health check support

### RestServer (`server.py`)

#### Primary Features

- Secure service deployment
- Rate limiting and CORS support
- Multi-layer middleware stack
- Comprehensive metrics collection
- Health check integration
- Request validation

#### Key Classes

1. **RestServerConfig**

   - Server deployment settings
   - Security configuration
   - Rate limiting parameters
   - CORS settings

   ```python
   @dataclass
   class RestServerConfig:
       host: str = "0.0.0.0"
       port: int = 8080
       mtls_config: Optional[MTLSConfig] = None
       security_policy: Optional[SecurityPolicy] = None
       cors_origins: Optional[list[str]] = None
       max_request_size: int = 1024 * 1024
   ```

2. **RateLimiter**

   - Token bucket algorithm
   - Per-client rate tracking
   - Burst handling
   - Memory optimization

3. **RestServer**
   - Middleware management
   - Route handling
   - Security validation
   - Health check support

## Security Features

### Authentication

- mTLS support
- Token validation
- Security context handling
- Client certificate verification

### Protection

- Rate limiting
- CORS configuration
- Request validation
- Error handling

### Monitoring

- Request metrics
- Performance tracking
- Security event logging
- Health status reporting

## Middleware Stack

### Order and Purpose

1. Security Middleware

   - Token validation
   - Request authentication
   - Security context propagation

2. Error Middleware

   - Exception handling
   - Error response formatting
   - Status code management

3. Rate Limit Middleware

   - Request throttling
   - Client identification
   - Burst handling

4. Metrics Middleware
   - Request timing
   - Status tracking
   - Performance metrics

## Implementation Details

### Client Usage

```python
# Initialize client with security
async with RestClient(RestClientConfig(
    base_url="https://service:8080",
    mtls_config=mtls_config,
    retry_policy=retry_policy
)) as client:
    # Make secure request
    response = await client.get(
        "api/resource",
        headers={"Authorization": "Bearer token"}
    )
```

### Server Setup

```python
# Initialize secure server
server = RestServer(
    config=RestServerConfig(
        port=8080,
        mtls_config=mtls_config,
        security_policy=security_policy
    ),
    security_validator=validator,
    metrics_collector=metrics
)

# Add routes and start
server.add_route("GET", "/api/resource", handler)
await server.start()
```

## Performance Considerations

### Optimizations

- Connection pooling
- Request pipelining
- Async operations
- Resource cleanup

### Resource Management

- Request size limits
- Connection pooling
- Memory usage controls
- Timeout management

## Best Practices

### Security

1. Enable mTLS in production
2. Configure strict CORS policies
3. Implement rate limiting
4. Use security middleware

### Performance

1. Set appropriate timeouts
2. Configure connection pools
3. Monitor resource usage
4. Implement circuit breakers

### Reliability

1. Use retry policies
2. Enable health checks
3. Monitor error rates
4. Handle backpressure

## Known Issues & Future Improvements

### Current Limitations

- Request prioritization needed
- Rate limiter memory usage
- Graceful shutdown support
- Connection draining

### Planned Enhancements

1. Request prioritization
2. Improved rate limiting
3. Graceful shutdown
4. Enhanced monitoring
5. Request validation

## Integration Points

### Service Mesh Core

- Service discovery
- Load balancing
- Health checking
- Metric collection

### Security Systems

- Certificate management
- Token validation
- Access control
- Audit logging

### Monitoring Stack

- Prometheus metrics
- Request tracing
- Performance monitoring
- Health status reporting

## WebSocket Support

### Features

- Secure WebSocket connections
- Heartbeat monitoring
- Connection management
- Error handling

### Usage Example

```python
# Establish WebSocket connection
ws = await client.websocket_connect(
    "ws/events",
    headers={"Authorization": "Bearer token"}
)

async for msg in ws:
    # Handle messages
    pass
```
