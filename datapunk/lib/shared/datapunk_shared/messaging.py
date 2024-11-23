from typing import Optional, Dict, Any, Callable
import aio_pika
from aio_pika import Connection, Channel, Queue, Message
import json
from .utils.retry import with_retry, RetryConfig

class MessageBroker:
    """Handles message queue operations with retry logic"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection: Optional[Connection] = None
        self.channel: Optional[Channel] = None
        self.queues: Dict[str, Queue] = {}
        self.retry_config = RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            max_delay=30.0
        )
    
    @with_retry(exceptions=(aio_pika.AMQPException,))
    async def initialize(self) -> None:
        """Initialize connection with retry logic"""
        self.connection = await aio_pika.connect_robust(
            host=self.config['host'],
            port=self.config['port'],
            login=self.config['user'],
            password=self.config['password'],
            virtualhost=self.config.get('vhost', '/'),
            timeout=self.config.get('timeout', 5.0)
        )
        
        self.channel = await self.connection.channel()
        await self.channel.set_qos(
            prefetch_count=self.config.get('prefetch_count', 100)
        )
    
    async def close(self) -> None:
        """Close connections"""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
    
    @with_retry(exceptions=(aio_pika.AMQPException,))
    async def declare_queue(self, name: str, durable: bool = True) -> Queue:
        """Declare queue with retry logic"""
        if not self.channel:
            raise RuntimeError("Message broker not initialized")
            
        queue = await self.channel.declare_queue(
            name=name,
            durable=durable,
            auto_delete=False
        )
        self.queues[name] = queue
        return queue
    
    @with_retry(exceptions=(aio_pika.AMQPException,))
    async def publish(self, queue_name: str, message: Dict[str, Any]) -> None:
        """Publish message with retry logic"""
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
        """Set up message consumer"""
        if queue_name not in self.queues:
            await self.declare_queue(queue_name)
            
        async def process_message(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    await callback(data)
                except Exception as e:
                    # Log error and possibly retry or move to DLQ
                    print(f"Error processing message: {str(e)}")
                    
        await self.queues[queue_name].consume(process_message) 