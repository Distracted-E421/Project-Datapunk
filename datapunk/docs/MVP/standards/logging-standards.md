# Logging Standards

## Purpose

Define consistent logging practices across all Datapunk services to ensure effective debugging, monitoring, and troubleshooting while maintaining security, compliance, and performance requirements.

## Log Levels

| Level   | Usage                                          | Example                                          | Alert Priority |
|---------|------------------------------------------------|--------------------------------------------------|----------------|
| ERROR   | Application errors requiring immediate attention | Database connection failure, API critical errors | High/Page     |
| WARNING | Potentially harmful situations                  | Rate limit approaching, high resource usage      | Medium/Notify  |
| INFO    | General operational events                      | Service start/stop, job completion               | None          |
| DEBUG   | Detailed information for debugging              | Function entry/exit, variable states             | None          |

## Log Format

### JSON Structure

```json
{
    "timestamp": "ISO8601",
    "level": "ERROR|WARNING|INFO|DEBUG",
    "service": "service_name",
    "trace_id": "uuid",
    "span_id": "uuid",
    "message": "Human readable message",
    "context": {
        "method": "HTTP method or function name",
        "path": "request path or module path",
        "duration_ms": 1234,
        "user_id": "uuid",
        "correlation_id": "uuid",
        "environment": "production|staging|development",
        "version": "service_version",
        "host": "server_hostname",
        "additional_data": {}
    },
    "error": {
        "type": "error_class_name",
        "message": "error_message",
        "stack_trace": "formatted_stack_trace",
        "code": "error_code"
    }
}
```

### Service-Specific Implementations

#### Python Services

```python
import structlog
import logging.config

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": [
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
            ]
        }
    },
    "handlers": {
        "json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        }
    },
    "loggers": {
        "": {
            "handlers": ["json"],
            "level": "INFO",
            "propagate": True
        }
    }
})

logger = structlog.get_logger()
```

#### Node.js Services

```javascript
const winston = require('winston');

const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    defaultMeta: { 
        service: 'service-name',
        environment: process.env.NODE_ENV 
    },
    transports: [
        new winston.transports.Console({
            handleExceptions: true,
            handleRejections: true
        })
    ]
});
```

## Log Collection and Storage

### Infrastructure

- Primary collector: Loki
- Secondary storage: Elasticsearch (for long-term storage)
- Retention periods:
  - ERROR: 365 days
  - WARNING: 90 days
  - INFO: 30 days
  - DEBUG: 7 days
- Log rotation:
  - Maximum file size: 100MB
  - Maximum files: 5
  - Compression: gzip

### Performance Considerations

- Batch logging for high-volume events
- Sampling for DEBUG level in production
- Async logging for non-critical events
- Log buffer size: 1000 events
- Maximum log size: 1MB per event

## Best Practices

1. Structured Logging
   - Always use JSON format
   - Include all required fields
   - Maintain consistent field names

2. Security and Privacy
   - Never log sensitive data (passwords, tokens, PII)
   - Mask sensitive fields (email, phone)
   - Include authentication context when relevant

3. Context and Correlation
   - Always include trace_id for request tracking
   - Add span_id for distributed tracing
   - Include correlation_id for related events

4. Error Logging
   - Include full stack traces
   - Add error codes
   - Provide error context
   - Include recovery actions taken

5. Performance Impact
   - Use appropriate log levels
   - Implement log sampling in high-traffic areas
   - Buffer non-critical logs
   - Use async logging where appropriate

## Integration Points

### Monitoring Integration

```yaml
monitoring_integration:
  metrics:
    - log_volume_per_level
    - logging_errors
    - logging_latency
  alerts:
    - log_pipeline_health
    - storage_capacity
    - error_rate_threshold
```

### Alert Correlation

```yaml
alert_correlation:
  error_patterns:
    - consecutive_errors: 5
    - error_rate: "10/minute"
    - pattern_matching: true
  notification_channels:
    - slack
    - pagerduty
    - email
```

## Compliance and Auditing

- Compliance with GDPR, CCPA, and HIPAA requirements
- Audit trail for security events
- Automated PII detection and masking
- Regular log review and analysis
- Retention policy enforcement

## Known Limitations

- Maximum event size: 1MB
- Rate limiting: 10,000 events/second per service
- Sampling may miss some DEBUG events
- Async logging may have slight delay
