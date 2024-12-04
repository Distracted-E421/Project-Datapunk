# Configuration Validation (config_validator.py)

## Purpose

Provides comprehensive configuration validation for the service mesh, ensuring proper setup of load balancing, retry policies, circuit breakers, and health checks.

## Context

Critical component for maintaining system reliability by validating and enforcing configuration standards across the service mesh infrastructure.

## Dependencies

- pydantic: For runtime validation
- pydantic_settings: For settings management
- Enum: For type safety

## Core Components

### LoadBalancingPolicy Enum

```python
class LoadBalancingPolicy(str, Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RESPONSE_TIME = "response_time"
    RANDOM = "random"
```

Defines supported load balancing strategies:

- Round-robin for even distribution
- Least connections for capacity-based routing
- Response time for latency-sensitive routing
- Random for testing environments

### RetryPolicy Model

```python
class RetryPolicy(BaseModel):
    max_attempts: int = Field(ge=1, le=10, default=3)
    base_delay: float = Field(ge=0.1, le=60.0, default=1.0)
    max_delay: float = Field(ge=1.0, le=300.0, default=30.0)
    conditions: List[str] = Field(
        default=["5xx", "connect-failure", "timeout"]
    )
```

Validates retry behavior configuration:

- Attempt limits
- Delay parameters
- Retry conditions

### CircuitBreakerPolicy Model

```python
class CircuitBreakerPolicy(BaseModel):
    failure_threshold: float = Field(ge=0.0, le=1.0, default=0.5)
    reset_timeout: float = Field(ge=1.0, le=300.0, default=30.0)
    half_open_max_calls: int = Field(ge=1, le=100, default=5)
    window_size: int = Field(ge=10, le=1000, default=100)
```

Defines circuit breaker parameters:

- Failure detection thresholds
- Recovery timeouts
- Testing parameters
- Monitoring windows

### HealthCheckPolicy Model

```python
class HealthCheckPolicy(BaseModel):
    interval: float = Field(ge=1.0, le=300.0, default=30.0)
    timeout: float = Field(ge=0.1, le=30.0, default=5.0)
    unhealthy_threshold: int = Field(ge=1, le=10, default=3)
    healthy_threshold: int = Field(ge=1, le=10, default=2)
```

Configures health monitoring:

- Check intervals
- Timeout settings
- Status thresholds

### ServiceConfig Model

```python
class ServiceConfig(BaseModel):
    name: str
    host: str
    port: int = Field(ge=1, le=65535)
    tags: List[str] = Field(default_factory=list)
    load_balancing: LoadBalancingPolicy = LoadBalancingPolicy.ROUND_ROBIN
    retry_policy: RetryPolicy = RetryPolicy()
    circuit_breaker: CircuitBreakerPolicy = CircuitBreakerPolicy()
    health_check: HealthCheckPolicy = HealthCheckPolicy()
```

Comprehensive service configuration:

- Basic service information
- Load balancing preferences
- Reliability policies
- Health monitoring

### MeshConfig Model

```python
class MeshConfig(BaseModel):
    services: Dict[str, ServiceConfig]
    global_retry_policy: Optional[RetryPolicy] = None
    global_circuit_breaker: Optional[CircuitBreakerPolicy] = None
    global_health_check: Optional[HealthCheckPolicy] = None
```

Complete mesh configuration:

- Service definitions
- Global policies
- Policy inheritance
- Validation rules

## Implementation Details

### Name Validation

```python
@validator('name')
def validate_name(cls, v):
    if not v.isalnum() or not v.islower():
        raise ValueError(
            'Service name must be lowercase alphanumeric'
        )
    return v
```

- Ensures DNS compatibility
- Enforces naming conventions
- Prevents invalid characters

### Policy Inheritance

```python
def merge_with_globals(self, service_name: str) -> ServiceConfig:
```

- Combines global and service-specific policies
- Applies inheritance rules
- Validates final configuration

## Performance Considerations

- Validation overhead during startup
- Memory usage for configuration storage
- Policy inheritance computation
- Validation caching opportunities

## Security Considerations

- Configuration source validation
- Secure policy inheritance
- Protected policy updates
- Access control for changes

## Known Issues

- Complex policy inheritance
- Validation performance at scale
- Dynamic update limitations
- Version compatibility

## Trade-offs and Design Decisions

### Validation Strategy

- **Decision**: Runtime validation with Pydantic
- **Rationale**: Type safety and clear errors
- **Trade-off**: Performance vs. safety

### Policy Inheritance

- **Decision**: Global with local override
- **Rationale**: Consistent defaults with flexibility
- **Trade-off**: Complexity vs. customization

### Configuration Format

- **Decision**: Structured class-based models
- **Rationale**: Type safety and validation
- **Trade-off**: Verbosity vs. clarity

## Future Improvements

1. Dynamic configuration updates
2. Enhanced validation rules
3. Custom policy validators
4. Configuration versioning
5. Migration support

## Example Usage

```python
# Create service configuration
service_config = ServiceConfig(
    name="api_service",
    host="api.local",
    port=8080,
    tags=["v1"],
    retry_policy=RetryPolicy(
        max_attempts=5,
        base_delay=0.5
    )
)

# Create mesh configuration
mesh_config = MeshConfig(
    services={"api_service": service_config},
    global_retry_policy=RetryPolicy(
        max_attempts=3
    )
)

# Get merged configuration
final_config = mesh_config.merge_with_globals("api_service")
```

## Related Components

- Service Mesh
- Load Balancer
- Circuit Breaker
- Health Monitor
- Retry Handler

## Testing Considerations

1. Validation rules
2. Policy inheritance
3. Edge cases
4. Error messages
5. Performance impact
6. Migration paths
7. Version compatibility

## Monitoring and Observability

- Validation failures
- Policy changes
- Inheritance patterns
- Performance metrics
- Error rates
- Configuration usage

## Deployment Considerations

1. Initial configuration
2. Policy distribution
3. Update strategy
4. Rollback support
5. Version management

## Error Handling

- Validation failures
- Inheritance errors
- Type mismatches
- Missing configurations
- Version conflicts
- Update failures
