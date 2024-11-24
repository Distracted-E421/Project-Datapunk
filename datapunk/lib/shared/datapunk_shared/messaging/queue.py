from typing import Any, Dict, List, Optional, Callable, TypeVar
import asyncio
import aio_pika
import structlog
from dataclasses import dataclass
from ..monitoring import MetricsClient
from ..tracing import TracingManager, trace_method

logger = structlog.get_logger()
T = TypeVar('T')

@dataclass
class QueueConfig:
    """Configuration for message queues."""
    name: str
    durable: bool = True
    auto_delete: bool = False
    max_priority: int = 10
    max_length: Optional[int] = None
    dead_letter_exchange: Optional[str] = None
    message_ttl: Optional[int] = None  # milliseconds
    max_retries: int = 3

class MessageQueue:
    """Implements message queue patterns with monitoring and tracing."""
    
    def __init__(self,
                 connection: aio_pika.Connection,
                 config: QueueConfig,
                 metrics: MetricsClient,
                 tracing: TracingManager):
        self.connection = connection
        self.config = config
        self.metrics = metrics
        self.tracing = tracing
        self.logger = logger.bind(queue=config.name)
        self.channel = None
        self.queue = None
        
    async def initialize(self):
        """Initialize queue and channel."""
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)
        
        # Declare dead letter exchange if configured
        if self.config.dead_letter_exchange:
            await self.channel.declare_exchange(
                self.config.dead_letter_exchange,
                aio_pika.ExchangeType.DIRECT,
                durable=True
            )
        
        # Declare main queue
        self.queue = await self.channel.declare_queue(
            self.config.name,
            durable=self.config.durable,
            auto_delete=self.config.auto_delete,
            arguments={
                'x-max-priority': self.config.max_priority,
                'x-max-length': self.config.max_length,
                'x-dead-letter-exchange': self.config.dead_letter_exchange,
                'x-message-ttl': self.config.message_ttl
            }
        )
    
    @trace_method("publish_message")
    async def publish(self,
                     message: Dict,
                     priority: int = 0,
                     correlation_id: Optional[str] = None) -> bool:
        """Publish message to queue."""
        try:
            # Create message with headers
            message_body = aio_pika.Message(
                body=message.encode(),
                priority=min(priority, self.config.max_priority),
                correlation_id=correlation_id,
                headers={
                    'retry_count': 0,
                    'original_timestamp': str(datetime.utcnow())
                }
            )
            
            # Publish with tracing context
            await self.channel.default_exchange.publish(
                message_body,
                routing_key=self.config.name
            )
            
            self.metrics.increment('messages_published_total',
                                 {'queue': self.config.name})
            return True
            
        except Exception as e:
            self.logger.error("message_publish_failed", error=str(e))
            self.metrics.increment('message_publish_failures_total',
                                 {'queue': self.config.name})
            raise
    
    @trace_method("consume_messages")
    async def consume(self,
                     callback: Callable[[Dict], Awaitable[None]],
                     error_callback: Optional[Callable[[Exception], Awaitable[None]]] = None):
        """Consume messages from queue."""
        async def _handle_message(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    # Extract message data and metadata
                    data = message.body.decode()
                    headers = message.headers or {}
                    retry_count = headers.get('retry_count', 0)
                    
                    # Add tracing context
                    self.tracing.set_attribute("message.id", message.message_id)
                    self.tracing.set_attribute("message.retry_count", retry_count)
                    
                    # Process message
                    await callback(data)
                    
                    # Record success metric
                    self.metrics.increment('messages_processed_total',
                                         {'queue': self.config.name})
                    
                except Exception as e:
                    self.logger.error("message_processing_failed",
                                    message_id=message.message_id,
                                    error=str(e))
                    
                    # Record failure metric
                    self.metrics.increment('message_processing_failures_total',
                                         {'queue': self.config.name})
                    
                    # Handle retry logic
                    if retry_count < self.config.max_retries:
                        await self._retry_message(message, retry_count + 1)
                    else:
                        await self._move_to_dlq(message)
                        
                    if error_callback:
                        await error_callback(e)
                    
                    raise
        
        await self.queue.consume(_handle_message)
    
    async def _retry_message(self,
                           message: aio_pika.IncomingMessage,
                           retry_count: int):
        """Retry failed message processing."""
        # Update headers for retry
        headers = message.headers or {}
        headers['retry_count'] = retry_count
        
        # Calculate delay with exponential backoff
        delay = min(10 * (2 ** retry_count), 300)  # Max 5 minutes
        
        # Create delayed message
        retry_message = aio_pika.Message(
            body=message.body,
            headers=headers,
            priority=message.priority,
            correlation_id=message.correlation_id,
            expiration=delay * 1000  # Convert to milliseconds
        )
        
        # Publish to delay queue
        await self.channel.default_exchange.publish(
            retry_message,
            routing_key=f"{self.config.name}.retry"
        )
        
        self.metrics.increment('message_retries_total',
                             {'queue': self.config.name})
    
    async def _move_to_dlq(self, message: aio_pika.IncomingMessage):
        """Move failed message to dead letter queue."""
        if self.config.dead_letter_exchange:
            # Add failure context to headers
            headers = message.headers or {}
            headers['final_failure_timestamp'] = str(datetime.utcnow())
            
            # Create DLQ message
            dlq_message = aio_pika.Message(
                body=message.body,
                headers=headers,
                priority=message.priority,
                correlation_id=message.correlation_id
            )
            
            # Publish to DLQ
            await self.channel.default_exchange.publish(
                dlq_message,
                routing_key=f"{self.config.name}.dlq"
            )
            
            self.metrics.increment('messages_moved_to_dlq_total',
                                 {'queue': self.config.name}) 