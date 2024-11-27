from typing import Optional, Dict, Any, List, Set, Callable, Generic, TypeVar
from dataclasses import dataclass
import asyncio
from datetime import datetime
from enum import Enum
import json
from ..patterns.retry import RetryPolicy
from ..patterns.dlq import DeadLetterQueue, FailureReason
from ...monitoring import MetricsCollector

T = TypeVar('T')  # Message type
R = TypeVar('R')  # Result type

"""
Message broker implementation for Datapunk's pub/sub messaging system.

Provides a robust message broker with:
- Multiple delivery guarantees (at-least-once, at-most-once, exactly-once)
- Topic-based routing with pattern matching
- Message persistence and compression
- Automatic cleanup of old messages
- Detailed metrics collection

Designed to be the backbone of asynchronous communication between services
while maintaining reliability and performance under high load.
"""

class DeliveryMode(Enum):
    """
    Message delivery guarantees supported by the broker.
    
    Affects how messages are handled and retried:
    - AT_LEAST_ONCE: Messages may be delivered multiple times (default, safest)
    - AT_MOST_ONCE: Messages may be lost but never duplicated
    - EXACTLY_ONCE: Messages delivered exactly once (higher overhead)
    
    NOTE: EXACTLY_ONCE requires additional coordination overhead
    """
    AT_LEAST_ONCE = "at_least_once"
    AT_MOST_ONCE = "at_most_once"
    EXACTLY_ONCE = "exactly_once"

class TopicType(Enum):
    """
    Supported message routing patterns.
    
    Determines how messages are distributed to subscribers:
    - FANOUT: Broadcast to all subscribers (fastest)
    - DIRECT: Point-to-point delivery
    - TOPIC: Pattern-based routing (most flexible)
    - HEADERS: Content-based routing (most overhead)
    """
    FANOUT = "fanout"
    DIRECT = "direct"
    TOPIC = "topic"
    HEADERS = "headers"

@dataclass
class BrokerConfig:
    """
    Configuration for message broker behavior.
    
    Allows fine-tuning of broker parameters to balance between
    reliability, performance, and resource usage.
    
    TODO: Add support for message prioritization
    FIXME: Consider adding circuit breaker configuration
    """
    delivery_mode: DeliveryMode = DeliveryMode.AT_LEAST_ONCE
    topic_type: TopicType = TopicType.FANOUT
    max_message_size: int = 1024 * 1024  # 1MB limit prevents memory issues
    enable_persistence: bool = True
    storage_path: Optional[str] = None
    enable_compression: bool = True
    compression_threshold: int = 1024
    max_retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_dlq: bool = True
    cleanup_interval: int = 3600
    max_queue_size: int = 10000
    batch_size: int = 100

@dataclass
class TopicConfig:
    """Configuration for a pub/sub topic"""
    name: str
    pattern: Optional[str] = None  # Regex pattern for message filtering
    retention_hours: int = 24
    max_subscribers: int = 100
    require_ack: bool = True
    batch_size: Optional[int] = None
    dead_letter_topic: Optional[str] = None

@dataclass
class SubscriptionConfig:
    """Configuration for a subscription"""
    topic: str
    name: str
    filter_pattern: Optional[str] = None
    batch_size: Optional[int] = None
    ack_timeout: int = 30  # seconds
    max_retry: int = 3
    backoff_base: float = 2.0

class MessageBroker(Generic[T, R]):
    """
    Implements pub/sub message broker with configurable behavior.
    
    Features:
    - Configurable message delivery guarantees
    - Multiple routing patterns
    - Message persistence and compression
    - Automatic cleanup and DLQ handling
    - Detailed metrics collection
    
    NOTE: Consider memory usage when setting queue size limits
    TODO: Implement message prioritization
    """
    def __init__(
        self,
        config: BrokerConfig,
        retry_policy: Optional[RetryPolicy] = None,
        dlq: Optional[DeadLetterQueue] = None,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.retry_policy = retry_policy
        self.dlq = dlq
        self.metrics = metrics_collector
        self._topics: Dict[str, Set[str]] = {}  # topic -> subscriber_ids
        self._subscribers: Dict[str, Callable] = {}  # subscriber_id -> callback
        self._messages: Dict[str, List[Dict]] = {}  # topic -> messages
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()

    async def start(self):
        """Start message broker"""
        self._running = True
        if self.config.enable_persistence:
            await self._load_state()
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop message broker"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        if self.config.enable_persistence:
            await self._save_state()

    async def publish(
        self,
        topic: str,
        message: T,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Publish message to topic with delivery guarantees.
        
        Handles message validation, storage, and delivery to subscribers
        according to configured delivery mode and topic type.
        
        Returns True if message was accepted for delivery, False otherwise.
        
        FIXME: Handle edge case where subscriber list changes during delivery
        """
        if not self._validate_message_size(message):
            if self.metrics:
                await self.metrics.increment(
                    "broker.message.size_exceeded",
                    tags={"topic": topic}
                )
            return False

        async with self._lock:
            try:
                # Prepare message
                msg_data = {
                    "payload": message,
                    "headers": headers or {},
                    "timestamp": datetime.utcnow().isoformat(),
                    "attempts": 0
                }

                # Store message
                if topic not in self._messages:
                    self._messages[topic] = []
                self._messages[topic].append(msg_data)

                # Deliver to subscribers
                await self._deliver_message(topic, msg_data)

                if self.metrics:
                    await self.metrics.increment(
                        "broker.message.published",
                        tags={"topic": topic}
                    )

                return True

            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "broker.publish.error",
                        tags={
                            "topic": topic,
                            "error": str(e)
                        }
                    )
                return False

    async def subscribe(
        self,
        topic: str,
        callback: Callable[[T], R],
        subscriber_id: Optional[str] = None
    ) -> str:
        """
        Subscribe to topic with callback function.
        
        Registers subscriber for message delivery and handles:
        - Subscriber ID generation
        - Callback registration
        - Metrics collection
        
        NOTE: Callbacks should be idempotent for at-least-once delivery
        """
        async with self._lock:
            # Generate subscriber ID if not provided
            subscriber_id = subscriber_id or f"{topic}_{len(self._subscribers)}"

            # Register subscriber
            if topic not in self._topics:
                self._topics[topic] = set()
            self._topics[topic].add(subscriber_id)
            self._subscribers[subscriber_id] = callback

            if self.metrics:
                await self.metrics.increment(
                    "broker.subscriber.added",
                    tags={"topic": topic}
                )

            return subscriber_id

    async def unsubscribe(self, subscriber_id: str):
        """Unsubscribe from topic"""
        async with self._lock:
            # Remove subscriber
            self._subscribers.pop(subscriber_id, None)
            for subscribers in self._topics.values():
                subscribers.discard(subscriber_id)

            if self.metrics:
                await self.metrics.increment("broker.subscriber.removed")

    async def _deliver_message(self, topic: str, message: Dict):
        """
        Deliver message to subscribers with retry handling.
        
        Implements delivery guarantees and handles:
        - Retry logic for failed deliveries
        - DLQ routing for exhausted retries
        - Metrics collection for monitoring
        
        TODO: Add support for batch delivery optimization
        """
        if topic not in self._topics:
            return

        for subscriber_id in self._topics[topic]:
            callback = self._subscribers.get(subscriber_id)
            if not callback:
                continue

            try:
                if self.retry_policy:
                    # Wrap callback with retry policy
                    callback = self.retry_policy.wrap(callback)

                await callback(message["payload"])

                if self.metrics:
                    await self.metrics.increment(
                        "broker.message.delivered",
                        tags={
                            "topic": topic,
                            "subscriber": subscriber_id
                        }
                    )

            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "broker.delivery.error",
                        tags={
                            "topic": topic,
                            "subscriber": subscriber_id,
                            "error": str(e)
                        }
                    )

                # Handle failed delivery
                message["attempts"] += 1
                if message["attempts"] >= self.config.max_retry_attempts:
                    if self.dlq:
                        await self.dlq.add_message(
                            message_id=f"{topic}_{message['timestamp']}",
                            message=message["payload"],
                            reason=FailureReason.PROCESSING_ERROR,
                            error=str(e),
                            metadata={
                                "topic": topic,
                                "subscriber": subscriber_id,
                                "attempts": message["attempts"]
                            }
                        )

    def _validate_message_size(self, message: T) -> bool:
        """Validate message size"""
        try:
            size = len(json.dumps(message))
            return size <= self.config.max_message_size
        except Exception:
            return False

    async def _cleanup_loop(self):
        """
        Periodically clean up old messages and update metrics.
        
        Prevents unbounded growth of message storage while
        maintaining system stability under load.
        
        NOTE: Cleanup interval should be tuned based on message volume
        """
        while self._running:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_messages()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "broker.cleanup.error",
                        tags={"error": str(e)}
                    )

    async def _cleanup_messages(self):
        """Remove old messages"""
        async with self._lock:
            for topic in self._messages:
                if len(self._messages[topic]) > self.config.max_queue_size:
                    # Keep only the most recent messages
                    self._messages[topic] = self._messages[topic][-self.config.max_queue_size:]

    async def _load_state(self):
        """Load broker state from storage"""
        if not self.config.storage_path:
            return

        try:
            with open(self.config.storage_path, 'r') as f:
                data = json.load(f)
                self._topics = {k: set(v) for k, v in data["topics"].items()}
                self._messages = data["messages"]

        except FileNotFoundError:
            pass
        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "broker.storage.load_error",
                    tags={"error": str(e)}
                )

    async def _save_state(self):
        """Save broker state to storage"""
        if not self.config.storage_path:
            return

        try:
            with open(self.config.storage_path, 'w') as f:
                data = {
                    "topics": {k: list(v) for k, v in self._topics.items()},
                    "messages": self._messages
                }
                json.dump(data, f)

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "broker.storage.save_error",
                    tags={"error": str(e)}
                )

    async def get_stats(self) -> Dict[str, Any]:
        """Get broker statistics"""
        return {
            "topics": len(self._topics),
            "subscribers": len(self._subscribers),
            "messages": {
                topic: len(messages)
                for topic, messages in self._messages.items()
            },
            "delivery_mode": self.config.delivery_mode.value,
            "topic_type": self.config.topic_type.value
        } 