from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
import asyncio
import aio_pika
import json
from datetime import datetime
from ..patterns.retry import MessageRetryPolicy
from ...monitoring import MetricsCollector

@dataclass
class QueueConfig:
    """Configuration for message queue"""
    url: str
    exchange_name: str = "datapunk"
    queue_prefix: str = "dp"
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    dead_letter_exchange: str = "datapunk.dlx"
    message_ttl: int = 24 * 60 * 60  # 24 hours in seconds
    enable_persistence: bool = True
    enable_priority: bool = True
    max_priority: int = 10
    batch_size: int = 100

class QueueManager:
    """Manages RabbitMQ connections and operations"""
    def __init__(
        self,
        config: QueueConfig,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.metrics = metrics_collector
        self._connection = None
        self._channel = None
        self._exchange = None
        self._dlx_exchange = None
        self._consumers: Dict[str, List[Callable]] = {}
        self._retry_policy = MessageRetryPolicy(
            max_retries=config.max_retries,
            retry_delay=config.retry_delay
        )

    async def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            self._connection = await aio_pika.connect_robust(self.config.url)
            self._channel = await self._connection.channel()
            
            # Declare exchanges
            self._exchange = await self._channel.declare_exchange(
                self.config.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=self.config.enable_persistence
            )
            
            self._dlx_exchange = await self._channel.declare_exchange(
                self.config.dead_letter_exchange,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            if self.metrics:
                await self.metrics.increment("messaging.connections.success")
                
        except Exception as e:
            if self.metrics:
                await self.metrics.increment("messaging.connections.failure")
            raise ConnectionError(f"Failed to connect to RabbitMQ: {str(e)}")

    async def close(self):
        """Close connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
            self._channel = None
            self._exchange = None
            self._dlx_exchange = None

    async def declare_queue(
        self,
        queue_name: str,
        routing_key: str,
        dead_letter: bool = True
    ):
        """Declare a queue with optional dead letter queue"""
        queue_args = {
            "x-message-ttl": self.config.message_ttl * 1000,  # Convert to milliseconds
            "x-max-priority": self.config.max_priority if self.config.enable_priority else None
        }
        
        if dead_letter:
            queue_args.update({
                "x-dead-letter-exchange": self.config.dead_letter_exchange,
                "x-dead-letter-routing-key": f"dlq.{routing_key}"
            })

        queue = await self._channel.declare_queue(
            f"{self.config.queue_prefix}.{queue_name}",
            durable=self.config.enable_persistence,
            arguments=queue_args
        )
        
        await queue.bind(self._exchange, routing_key)
        
        # Declare corresponding dead letter queue if needed
        if dead_letter:
            dlq = await self._channel.declare_queue(
                f"{self.config.queue_prefix}.dlq.{queue_name}",
                durable=True
            )
            await dlq.bind(self._dlx_exchange, f"dlq.{routing_key}")

        return queue

    async def publish(
        self,
        routing_key: str,
        message: Dict[str, Any],
        priority: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """Publish message to exchange"""
        try:
            message_body = json.dumps(message).encode()
            
            # Prepare message properties
            properties = {
                "delivery_mode": 2 if self.config.enable_persistence else 1,
                "timestamp": datetime.utcnow().timestamp(),
                "headers": headers or {}
            }
            
            if priority is not None and self.config.enable_priority:
                properties["priority"] = min(priority, self.config.max_priority)

            await self._exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    **properties
                ),
                routing_key=routing_key
            )
            
            if self.metrics:
                await self.metrics.increment(
                    "messaging.publish.success",
                    tags={"routing_key": routing_key}
                )
                
        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "messaging.publish.failure",
                    tags={"routing_key": routing_key, "error": str(e)}
                )
            raise

    async def subscribe(
        self,
        queue_name: str,
        routing_key: str,
        callback: Callable,
        batch_size: Optional[int] = None
    ):
        """Subscribe to queue with callback"""
        queue = await self.declare_queue(queue_name, routing_key)
        
        # Store callback for reconnection handling
        if queue_name not in self._consumers:
            self._consumers[queue_name] = []
        self._consumers[queue_name].append(callback)
        
        async def message_handler(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    # Parse message
                    body = json.loads(message.body.decode())
                    
                    # Process with retry policy
                    await self._retry_policy.execute(
                        callback,
                        body,
                        message.headers
                    )
                    
                    if self.metrics:
                        await self.metrics.increment(
                            "messaging.consume.success",
                            tags={"queue": queue_name}
                        )
                        
                except Exception as e:
                    if self.metrics:
                        await self.metrics.increment(
                            "messaging.consume.failure",
                            tags={"queue": queue_name, "error": str(e)}
                        )
                    # Message will be moved to DLQ after max retries
                    raise

        # Set up consumer with optional batching
        if batch_size or self.config.batch_size > 1:
            await queue.consume(
                message_handler,
                batch_size=batch_size or self.config.batch_size
            )
        else:
            await queue.consume(message_handler)

    async def handle_dlq(
        self,
        queue_name: str,
        handler: Callable
    ):
        """Set up handler for dead letter queue"""
        dlq = await self._channel.declare_queue(
            f"{self.config.queue_prefix}.dlq.{queue_name}",
            durable=True
        )
        
        async def dlq_handler(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    body = json.loads(message.body.decode())
                    await handler(body, message.headers)
                    
                    if self.metrics:
                        await self.metrics.increment(
                            "messaging.dlq.handled",
                            tags={"queue": queue_name}
                        )
                        
                except Exception as e:
                    if self.metrics:
                        await self.metrics.increment(
                            "messaging.dlq.failed",
                            tags={"queue": queue_name, "error": str(e)}
                        )
                    raise

        await dlq.consume(dlq_handler) 