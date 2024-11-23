# Retry Policy Standards

## Purpose
Define standardized retry mechanisms across all Datapunk services to ensure resilient service communication with distributed coordination and idempotency guarantees.

## Context
This document outlines retry policies used in service-to-service communication, focusing on coordinated retries in a distributed system.

## Design/Details

### 1. Retry Configuration Levels

```yaml
retry_policies:
  default:
    max_attempts: 3
    initial_delay: 0.1
    max_delay: 10.0
    exponential_base: 2
    jitter: true
    jitter_factor: 0.1
    # New distributed settings
    slot_count: 10
    slot_width: 0.1
    coordination_enabled: true
    idempotency_ttl: 3600

  aggressive:
    max_attempts: 5
    initial_delay: 0.05
    max_delay: 5.0
    exponential_base: 1.5
    jitter: true
    jitter_factor: 0.1
    slot_count: 20
    slot_width: 0.05
    coordination_enabled: true
    idempotency_ttl: 1800

  conservative:
    max_attempts: 2
    initial_delay: 0.5
    max_delay: 15.0
    exponential_base: 2
    jitter: true
    jitter_factor: 0.05
    slot_count: 5
    slot_width: 0.2
    coordination_enabled: true
    idempotency_ttl: 7200
```

### 2. Required Components

```yaml
components:
  coordination:
    type: "redis"
    required: true
    purpose: "Distributed retry coordination"
    
  idempotency:
    type: "redis"
    required: true
    purpose: "Operation deduplication"
    
  time_sync:
    type: "ntp"
    required: false
    purpose: "Clock skew mitigation"
```

### 2. Implementation Patterns

#### Decorator Usage
```python
@with_retry(
    retry_config=RetryConfig(max_attempts=3),
    retry_on=(aiohttp.ClientError, asyncio.TimeoutError),
    service_name="lake"
)
async def call_service():
    # Service call implementation
```

#### Direct Usage
```python
retry_policy = RetryPolicy(RetryConfig(max_attempts=3))
result = await retry_policy.execute_with_retry(
    operation=service_call,
    service_name="stream",
    operation_name="data_fetch"
)
```

### 3. Metrics Collection

```yaml
retry_metrics:
  counters:
    - name: retry_attempts_total
      labels: [service, operation, attempt]
    - name: retry_success_total
      labels: [service, operation, attempts_needed]
    - name: retry_failure_total
      labels: [service, operation, error_type]
  
  histograms:
    - name: retry_duration_seconds
      labels: [service, operation]
      buckets: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
```

### 4. Error Categories

```yaml
retry_error_categories:
  retryable:
    - ConnectionError
    - TimeoutError
    - ServiceUnavailableError
    - RateLimitExceededError
  
  non_retryable:
    - AuthenticationError
    - ValidationError
    - ResourceNotFoundError
    - BusinessLogicError
```

## Prerequisites

### Dependencies
- Python 3.11+
- `structlog` for logging
- `prometheus_client` for metrics
- `asyncio` for async support

### Configuration
```python
required_environment_variables = {
    "RETRY_MAX_ATTEMPTS": "3",
    "RETRY_INITIAL_DELAY": "0.1",
    "RETRY_MAX_DELAY": "10.0"
}
```

## Testing Notes

### Unit Test Cases
```python
test_scenarios = [
    "successful_operation_no_retries",
    "success_after_retries",
    "max_retries_exceeded",
    "backoff_timing_verification",
    "jitter_distribution_check"
]
```

### Integration Test Scenarios
```yaml
integration_tests:
  - scenario: "service_temporary_unavailable"
    expected: "success_after_retries"
  - scenario: "network_timeout"
    expected: "exponential_backoff_visible"
  - scenario: "rate_limit_exceeded"
    expected: "respect_retry_after_header"
```

## Error Handling and Logging

### Log Format
```json
{
    "timestamp": "ISO8601",
    "level": "INFO|WARNING|ERROR",
    "service": "service_name",
    "operation": "operation_name",
    "attempt": 1,
    "delay": 0.1,
    "error": "error_message",
    "trace_id": "uuid"
}
```

### Monitoring Integration
```yaml
monitoring:
  alerts:
    - name: "HighRetryRate"
      condition: "retry_attempts_total > threshold"
      severity: "warning"
    - name: "RetryExhaustion"
      condition: "retry_failure_total > threshold"
      severity: "critical"
```

## Performance Considerations

1. **Backoff Strategy**
   - Exponential backoff prevents thundering herd
   - Jitter reduces coordination between retrying clients
   - Max delay cap prevents excessive wait times

2. **Resource Impact**
   - Memory: O(1) per retry policy instance
   - CPU: Minimal computation for delay calculation
   - Network: Reduced load through backoff

## Security Considerations

1. **Rate Limiting**
   - Respect service rate limits
   - Honor Retry-After headers
   - Implement circuit breakers

2. **Authentication**
   - Retry authentication failures only when token refresh needed
   - Do not retry on permanent auth failures

## Known Issues

1. **Edge Cases**
   - Race conditions in distributed retries
   - Potential for duplicate operations
   - Clock skew impact on timing

2. **Limitations**
   - No guaranteed delivery
   - No persistent retry queue
   - No cross-process coordination

## Future Enhancements

1. **Planned Features**
   - Persistent retry queue
   - Retry policy inheritance
   - Dynamic policy adjustment
   - Circuit breaker integration

2. **Integration Points**
   - Service mesh integration
   - Distributed tracing correlation
   - Metrics aggregation
   - Alert rule automation

## Usage Examples

### Basic Implementation
```python
@with_retry(
    retry_config=RetryConfig(),
    service_name="example"
)
async def basic_operation():
    return await make_request()
```

### Advanced Configuration
```python
@with_retry(
    retry_config=RetryConfig(
        max_attempts=5,
        initial_delay=0.1,
        max_delay=5.0,
        jitter=True
    ),
    retry_on=(CustomError, TimeoutError),
    service_name="advanced",
    operation_name="complex_operation"
)
async def advanced_operation():
    return await complex_request()
```

### Error Handling
```python
try:
    result = await operation_with_retry()
except MaxRetriesExceeded as e:
    logger.error("Operation failed after max retries", error=str(e))
    # Handle failure
``` 