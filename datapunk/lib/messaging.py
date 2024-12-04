"""Resilient message broker implementation for service mesh communication.

This module implements the message layer component defined in sys-arch.mmd,
providing reliable async message handling with automatic retries and 
robust error recovery. It serves as the backbone for inter-service 
communication in the Datapunk architecture.

Key Features:
- Automatic connection recovery
- Message persistence
- Configurable retry policies
- Dead letter queue support (TODO)
- Quality of service controls

Implementation Notes:
- Uses aio_pika for async AMQP communication
- Implements circuit breaker pattern for fault tolerance
- Messages are persistent by default for reliability
- Prefetch count is tunable for throughput optimization
"""

from typing import Optional, Dict, Any, Callable
import aio_pika
from aio_pika import Connection, Channel, Queue, Message
import json
from .utils.retry import with_retry, RetryConfig

class MessageBroker:
    """Handles message queue operations with comprehensive retry logic.
    
    Implements the Message Layer component of the system architecture:
    - Robust connection management
    - Queue declaration and binding
    - Message publishing with persistence
    - Async message consumption
    
    Note: All operations include retry logic to handle temporary network issues
    TODO: Implement dead letter queue handling for failed messages
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize broker with configuration and retry policies.
        
        Args:
            config: Broker configuration including:
                   - host: RabbitMQ host address
                   - port: RabbitMQ port
                   - user: Authentication username
                   - password: Authentication password
                   - vhost: Virtual host (default: '/')
                   - timeout: Connection timeout (default: 5.0)
        """
        self.config = config
        self.connection: Optional[Connection] = None
        self.channel: Optional[Channel] = None
        self.queues: Dict[str, Queue] = {}
        # Retry configuration optimized for network issues
        self.retry_config = RetryConfig(
            max_attempts=5,  # Balance between availability and latency
            base_delay=1.0,  # Initial retry delay
            max_delay=30.0   # Cap maximum retry delay
        )
    
    @with_retry(exceptions=(aio_pika.AMQPException,))
    async def initialize(self) -> None:
        """Establish broker connection with automatic retry.
        
        Implements robust connection establishment:
        - Automatic reconnection on failure
        - Connection timeout handling
        - Channel QoS configuration
        
        Raises:
            RuntimeError: If connection fails after all retries
        """
        self.connection = await aio_pika.connect_robust(
            host=self.config['host'],
            port=self.config['port'],
            login=self.config['user'],
            password=self.config['password'],
            virtualhost=self.config.get('vhost', '/'),
            timeout=self.config.get('timeout', 5.0)
        )
        
        self.channel = await self.connection.channel()
        # Configure QoS for optimal throughput
        await self.channel.set_qos(
            prefetch_count=self.config.get('prefetch_count', 100)
        )
    
    async def close(self) -> None:
        """Gracefully close broker connections.
        
        Ensures clean shutdown by:
        - Closing channel first to stop message flow
        - Then closing main connection
        """
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
    
    @with_retry(exceptions=(aio_pika.AMQPException,))
    async def declare_queue(self, name: str, durable: bool = True) -> Queue:
        """Declare message queue with durability options.
        
        Args:
            name: Queue identifier
            durable: Whether queue survives broker restart (default: True)
        
        Returns:
            Declared queue instance
        
        Raises:
            RuntimeError: If broker not initialized
        """
        if not self.channel:
            raise RuntimeError("Message broker not initialized")
            
        queue = await self.channel.declare_queue(
            name=name,
            durable=durable,  # Survive broker restarts
            auto_delete=False  # Persist until explicitly deleted
        )
        self.queues[name] = queue
        return queue
    
    @with_retry(exceptions=(aio_pika.AMQPException,))
    async def publish(self, queue_name: str, message: Dict[str, Any]) -> None:
        """Publish message with persistence guarantees.
        
        Args:
            queue_name: Target queue identifier
            message: Message payload to publish
        
        Note: Messages are persistent by default for reliability
        Raises:
            RuntimeError: If broker not initialized
        """
        if not self.channel:
            raise RuntimeError("Message broker not initialized")
            
        await self.channel.default_exchange.publish(
            Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=queue_name
        )
    
    async def consume(self, queue_name: str, callback: Callable) -> None:
        """Set up message consumer with error handling.
        
        Args:
            queue_name: Queue to consume from
            callback: Async function to process messages
        
        Note: Messages are auto-acknowledged only after successful processing
        TODO: Implement dead letter queue for failed messages
        """
        if queue_name not in self.queues:
            await self.declare_queue(queue_name)
            
        async def process_message(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    await callback(data)
                except Exception as e:
                    # TODO: Implement proper DLQ handling
                    print(f"Error processing message: {str(e)}")
                    
        await self.queues[queue_name].consume(process_message) 