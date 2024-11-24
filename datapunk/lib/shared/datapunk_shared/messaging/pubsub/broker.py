from typing import Dict, List, Any, Optional, Callable, Pattern
import asyncio
import re
from dataclasses import dataclass
import json
from datetime import datetime
from ..queue.manager import QueueManager, QueueConfig
from ...monitoring import MetricsCollector

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

class PubSubBroker:
    """Manages pub/sub topics and subscriptions"""
    def __init__(
        self,
        queue_manager: QueueManager,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.queue_manager = queue_manager
        self.metrics = metrics_collector
        self._topics: Dict[str, TopicConfig] = {}
        self._subscribers: Dict[str, Dict[str, SubscriptionConfig]] = {}
        self._filters: Dict[str, Pattern] = {}
        self._handlers: Dict[str, List[Callable]] = {}
        self._active_subscriptions: Dict[str, asyncio.Task] = {}

    async def create_topic(self, config: TopicConfig):
        """Create a new topic"""
        if config.name in self._topics:
            raise ValueError(f"Topic {config.name} already exists")

        # Compile filter pattern if provided
        if config.pattern:
            try:
                self._filters[config.name] = re.compile(config.pattern)
            except re.error as e:
                raise ValueError(f"Invalid topic pattern: {str(e)}")

        # Create underlying queue
        await self.queue_manager.declare_queue(
            queue_name=f"topic.{config.name}",
            routing_key=config.name,
            dead_letter=bool(config.dead_letter_topic)
        )

        self._topics[config.name] = config

        if self.metrics:
            await self.metrics.increment(
                "pubsub.topics.created",
                tags={"topic": config.name}
            )

    async def delete_topic(self, topic_name: str):
        """Delete a topic and all its subscriptions"""
        if topic_name not in self._topics:
            raise ValueError(f"Topic {topic_name} does not exist")

        # Cancel all active subscriptions
        for sub_name in self._subscribers.get(topic_name, {}):
            await self.unsubscribe(topic_name, sub_name)

        # Clean up resources
        del self._topics[topic_name]
        self._subscribers.pop(topic_name, None)
        self._filters.pop(topic_name, None)
        self._handlers.pop(topic_name, None)

        if self.metrics:
            await self.metrics.increment(
                "pubsub.topics.deleted",
                tags={"topic": topic_name}
            )

    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ):
        """Publish message to topic"""
        if topic not in self._topics:
            raise ValueError(f"Topic {topic} does not exist")

        # Check message against topic pattern
        if self._filters.get(topic):
            message_str = json.dumps(message)
            if not self._filters[topic].search(message_str):
                raise ValueError("Message does not match topic pattern")

        # Add metadata
        full_message = {
            "payload": message,
            "metadata": {
                "topic": topic,
                "timestamp": datetime.utcnow().isoformat(),
                "headers": headers or {}
            }
        }

        try:
            await self.queue_manager.publish(
                routing_key=topic,
                message=full_message,
                headers=headers
            )

            if self.metrics:
                await self.metrics.increment(
                    "pubsub.messages.published",
                    tags={"topic": topic}
                )

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "pubsub.messages.publish_failed",
                    tags={"topic": topic, "error": str(e)}
                )
            raise

    async def subscribe(
        self,
        config: SubscriptionConfig,
        handler: Callable[[Dict[str, Any], Dict[str, str]], Any]
    ):
        """Subscribe to topic with handler"""
        if config.topic not in self._topics:
            raise ValueError(f"Topic {config.topic} does not exist")

        topic_config = self._topics[config.topic]
        
        # Check subscription limits
        current_subs = len(self._subscribers.get(config.topic, {}))
        if current_subs >= topic_config.max_subscribers:
            raise ValueError(f"Maximum subscribers reached for topic {config.topic}")

        # Compile subscription filter if provided
        sub_filter = None
        if config.filter_pattern:
            try:
                sub_filter = re.compile(config.filter_pattern)
            except re.error as e:
                raise ValueError(f"Invalid subscription pattern: {str(e)}")

        # Store subscription
        if config.topic not in self._subscribers:
            self._subscribers[config.topic] = {}
        self._subscribers[config.topic][config.name] = config

        # Create subscription handler
        async def subscription_handler(message: Dict[str, Any], headers: Dict[str, str]):
            try:
                # Apply subscription filter
                if sub_filter:
                    message_str = json.dumps(message["payload"])
                    if not sub_filter.search(message_str):
                        return

                # Process message
                await handler(message["payload"], message["metadata"])

                if self.metrics:
                    await self.metrics.increment(
                        "pubsub.messages.processed",
                        tags={
                            "topic": config.topic,
                            "subscription": config.name
                        }
                    )

            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "pubsub.messages.processing_failed",
                        tags={
                            "topic": config.topic,
                            "subscription": config.name,
                            "error": str(e)
                        }
                    )
                raise

        # Start subscription
        subscription_task = asyncio.create_task(
            self.queue_manager.subscribe(
                queue_name=f"sub.{config.topic}.{config.name}",
                routing_key=config.topic,
                callback=subscription_handler,
                batch_size=config.batch_size
            )
        )

        self._active_subscriptions[f"{config.topic}.{config.name}"] = subscription_task

        if self.metrics:
            await self.metrics.increment(
                "pubsub.subscriptions.created",
                tags={"topic": config.topic, "subscription": config.name}
            )

    async def unsubscribe(self, topic: str, subscription_name: str):
        """Unsubscribe from topic"""
        if topic not in self._subscribers:
            return

        if subscription_name not in self._subscribers[topic]:
            return

        # Cancel subscription task
        sub_key = f"{topic}.{subscription_name}"
        if sub_key in self._active_subscriptions:
            self._active_subscriptions[sub_key].cancel()
            del self._active_subscriptions[sub_key]

        # Clean up subscription
        del self._subscribers[topic][subscription_name]
        if not self._subscribers[topic]:
            del self._subscribers[topic]

        if self.metrics:
            await self.metrics.increment(
                "pubsub.subscriptions.deleted",
                tags={"topic": topic, "subscription": subscription_name}
            )

    async def get_topic_stats(self, topic: str) -> Dict[str, Any]:
        """Get statistics for a topic"""
        if topic not in self._topics:
            raise ValueError(f"Topic {topic} does not exist")

        return {
            "name": topic,
            "config": vars(self._topics[topic]),
            "subscriber_count": len(self._subscribers.get(topic, {})),
            "subscribers": list(self._subscribers.get(topic, {}).keys()),
            "has_filter": bool(self._filters.get(topic))
        } 