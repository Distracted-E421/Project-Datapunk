# Message Queue Standards

## Purpose

Define standardized message patterns and configurations for reliable asynchronous communication between services.

## Context

Message queues serve as the backbone for asynchronous operations, event-driven architectures, and service decoupling.

## Design/Details

### 1. Queue Types

```yaml
queue_types:
  command:
    type: "direct"
    durability: true
    purpose: "Service-to-service commands"
    patterns:
      - "RPC-style calls"
      - "Task delegation"
    
  event:
    type: "topic"
    durability: true
    purpose: "Event broadcasting"
    patterns:
      - "State changes"
      - "System events"
    
  stream:
    type: "stream"
    durability: true
    purpose: "Data streaming"
    patterns:
      - "Log aggregation"
      - "Metrics collection"
```

### 2. Message Structure

```json
{
  "metadata": {
    "message_id": "uuid",
    "correlation_id": "uuid",
    "timestamp": "ISO8601",
    "source_service": "string",
    "target_service": "string",
    "message_type": "command|event|stream",
    "version": "1.0"
  },
  "payload": {
    "type": "string",
    "data": {},
    "schema_version": "string"
  },
  "tracing": {
    "trace_id": "string",
    "span_id": "string",
    "parent_id": "string"
  }
}
```

### 3. Exchange Patterns

```yaml
exchange_patterns:
  direct:
    name_format: "dp.command.{service}"
    binding_key: "{service}.{operation}"
    
  topic:
    name_format: "dp.event.{domain}"
    binding_key: "{service}.{event_type}.{severity}"
    
  fanout:
    name_format: "dp.broadcast.{type}"
    binding_key: null
```

### 4. Error Handling

```yaml
error_handling:
  dead_letter:
    exchange: "dp.dlx"
    queue_format: "dp.dlq.{original_queue}"
    retry_count: 3
    
  retry_policy:
    initial_delay: 1000
    multiplier: 2
    max_delay: 60000
    
  poison_message:
    action: "move_to_parking"
    notification: true
```

### 5. Quality of Service

```yaml
qos_settings:
  persistence:
    durable: true
    auto_delete: false
    
  delivery:
    acknowledgment: true
    prefetch_count: 10
    
  priority:
    enabled: true
    levels: 10
```

## Implementation Patterns

### 1. Publisher Pattern

```python
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class PublishConfig:
    exchange: str
    routing_key: str
    priority: Optional[int] = None
    ttl: Optional[int] = None

class Publisher:
    async def publish(self,
                     message: Any,
                     config: PublishConfig,
                     correlation_id: Optional[str] = None) -> None:
        """Publish message with standard metadata."""
        formatted_message = self.format_message(
            message,
            correlation_id=correlation_id
        )
        
        properties = self.create_properties(config)
        await self.channel.basic_publish(
            exchange=config.exchange,
            routing_key=config.routing_key,
            body=formatted_message,
            properties=properties
        )
```

### 2. Consumer Pattern

```python
class Consumer:
    async def consume(self,
                     queue: str,
                     callback: Callable,
                     prefetch: int = 10) -> None:
        """Set up consumer with standard configuration."""
        await self.channel.basic_qos(
            prefetch_count=prefetch
        )
        
        await self.channel.basic_consume(
            queue=queue,
            callback=self.wrap_callback(callback)
        )
    
    def wrap_callback(self, callback: Callable) -> Callable:
        """Wrap callback with error handling and tracing."""
        async def wrapped(message: Any) -> None:
            try:
                with self.tracer.start_span() as span:
                    await callback(message)
                    await message.ack()
            except Exception as e:
                await self.handle_consumer_error(message, e)
        return wrapped
```

## Error Handling and Recovery

### 1. Message Recovery

```python
class MessageRecovery:
    async def handle_failed_message(self,
                                  message: Any,
                                  error: Exception) -> None:
        """Handle failed message processing."""
        retry_count = self.get_retry_count(message)
        
        if retry_count < self.max_retries:
            await self.schedule_retry(message, retry_count)
        else:
            await self.move_to_dlq(message, error)
```

### 2. Circuit Breaking

```python
class MessageCircuitBreaker:
    async def check_health(self, exchange: str) -> bool:
        """Check exchange health before publishing."""
        if self.is_open(exchange):
            return False
            
        error_rate = await self.get_error_rate(exchange)
        if error_rate > self.threshold:
            self.open_circuit(exchange)
            return False
            
        return True
```

## Monitoring and Metrics

```yaml
monitoring_metrics:
  publish:
    - name: "message_publish_total"
      type: "counter"
      labels: ["exchange", "routing_key"]
    
    - name: "publish_latency_seconds"
      type: "histogram"
      labels: ["exchange"]
      
  consume:
    - name: "message_consume_total"
      type: "counter"
      labels: ["queue", "status"]
    
    - name: "processing_duration_seconds"
      type: "histogram"
      labels: ["queue", "message_type"]
```

## Security Considerations

```yaml
security:
  authentication:
    mechanism: "PLAIN"
    ssl_required: true
    
  authorization:
    vhost_isolation: true
    permission_patterns:
      read: "^dp\.{service}\."
      write: "^dp\.{service}\."
      
  encryption:
    in_transit: true
    at_rest: true
```

## Known Issues and Mitigations

### 1. Message Loss Prevention

```python
class MessageGuarantee:
    async def publish_with_confirmation(self,
                                      message: Any,
                                      config: PublishConfig) -> bool:
        """Publish with publisher confirms."""
        await self.channel.confirm_delivery()
        
        try:
            await self.publish(message, config)
            return True
        except Exception as e:
            await self.handle_publish_failure(message, config, e)
            return False
```

### 2. Queue Overflow Protection

```python
class OverflowProtection:
    async def check_queue_size(self, queue: str) -> bool:
        """Check queue size before publishing."""
        stats = await self.get_queue_stats(queue)
        
        if stats.message_count > self.max_queue_size:
            await self.handle_overflow(queue)
            return False
            
        return True
```
