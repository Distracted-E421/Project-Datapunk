from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
import asyncio
import json
from datetime import datetime, timedelta
from ..queue.manager import QueueManager
from .broker import TopicConfig, SubscriptionConfig
from ...monitoring import MetricsCollector

@dataclass
class SubscriberConfig:
    """Configuration for subscriber"""
    client_id: str
    max_concurrent: int = 10
    prefetch_count: int = 100
    auto_ack: bool = False
    process_timeout: int = 30  # seconds
    retry_delay: int = 5  # seconds
    max_retries: int = 3
    enable_dead_letter: bool = True
    enable_batch_processing: bool = False
    batch_size: int = 100
    batch_timeout: float = 1.0  # seconds

class MessageProcessor:
    """Base class for message processing"""
    async def process(self, message: Dict[str, Any], metadata: Dict[str, Any]) -> bool:
        """Process a message - override this method"""
        raise NotImplementedError()

    async def process_batch(
        self,
        messages: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> List[bool]:
        """Process a batch of messages - override for custom batch processing"""
        results = []
        for message in messages:
            try:
                success = await self.process(message, metadata)
                results.append(success)
            except Exception:
                results.append(False)
        return results

class Subscriber:
    """Manages message subscriptions and processing"""
    def __init__(
        self,
        config: SubscriberConfig,
        queue_manager: QueueManager,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.queue_manager = queue_manager
        self.metrics = metrics_collector
        self._processors: Dict[str, MessageProcessor] = {}
        self._active_subscriptions: Dict[str, asyncio.Task] = {}
        self._batch_queues: Dict[str, asyncio.Queue] = {}
        self._processing_semaphore = asyncio.Semaphore(config.max_concurrent)
        self._stopping = False

    async def subscribe(
        self,
        subscription: SubscriptionConfig,
        processor: MessageProcessor
    ):
        """Subscribe to a topic with a message processor"""
        if subscription.name in self._processors:
            raise ValueError(f"Subscription {subscription.name} already exists")

        self._processors[subscription.name] = processor

        # Set up batch processing queue if needed
        if self.config.enable_batch_processing:
            self._batch_queues[subscription.name] = asyncio.Queue(
                maxsize=self.config.batch_size
            )
            # Start batch processor
            self._active_subscriptions[f"{subscription.name}_batch"] = asyncio.create_task(
                self._batch_processor(subscription)
            )

        # Create subscription handler
        async def message_handler(message: Dict[str, Any], headers: Dict[str, str]):
            async with self._processing_semaphore:
                try:
                    if self.config.enable_batch_processing:
                        # Add to batch queue
                        await self._batch_queues[subscription.name].put(
                            (message, headers)
                        )
                        return

                    # Process individual message
                    success = await self._process_message(
                        message,
                        headers,
                        processor,
                        subscription
                    )

                    if self.metrics:
                        await self.metrics.increment(
                            "subscriber.messages.processed",
                            tags={
                                "subscription": subscription.name,
                                "success": str(success)
                            }
                        )

                except Exception as e:
                    if self.metrics:
                        await self.metrics.increment(
                            "subscriber.messages.failed",
                            tags={
                                "subscription": subscription.name,
                                "error": str(e)
                            }
                        )
                    raise

        # Start subscription
        self._active_subscriptions[subscription.name] = asyncio.create_task(
            self.queue_manager.subscribe(
                queue_name=f"sub.{subscription.name}",
                routing_key=subscription.topic,
                callback=message_handler,
                batch_size=None if self.config.enable_batch_processing else subscription.batch_size
            )
        )

    async def unsubscribe(self, subscription_name: str):
        """Unsubscribe from a topic"""
        if subscription_name not in self._processors:
            return

        # Cancel subscription tasks
        if subscription_name in self._active_subscriptions:
            self._active_subscriptions[subscription_name].cancel()
            del self._active_subscriptions[subscription_name]

        # Cancel batch processor if exists
        batch_key = f"{subscription_name}_batch"
        if batch_key in self._active_subscriptions:
            self._active_subscriptions[batch_key].cancel()
            del self._active_subscriptions[batch_key]

        # Clean up
        del self._processors[subscription_name]
        self._batch_queues.pop(subscription_name, None)

        if self.metrics:
            await self.metrics.increment(
                "subscriber.unsubscribed",
                tags={"subscription": subscription_name}
            )

    async def _process_message(
        self,
        message: Dict[str, Any],
        headers: Dict[str, str],
        processor: MessageProcessor,
        subscription: SubscriptionConfig,
        retry_count: int = 0
    ) -> bool:
        """Process a single message with retry logic"""
        try:
            # Apply message filter if configured
            if subscription.filter_pattern:
                message_str = json.dumps(message)
                if not subscription.filter_pattern.search(message_str):
                    return True  # Skip filtered messages

            # Process with timeout
            success = await asyncio.wait_for(
                processor.process(message, headers),
                timeout=self.config.process_timeout
            )

            if not success and retry_count < self.config.max_retries:
                # Retry after delay
                await asyncio.sleep(
                    self.config.retry_delay * (2 ** retry_count)  # Exponential backoff
                )
                return await self._process_message(
                    message,
                    headers,
                    processor,
                    subscription,
                    retry_count + 1
                )

            return success

        except asyncio.TimeoutError:
            if self.metrics:
                await self.metrics.increment(
                    "subscriber.messages.timeout",
                    tags={"subscription": subscription.name}
                )
            return False

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "subscriber.messages.error",
                    tags={
                        "subscription": subscription.name,
                        "error": str(e)
                    }
                )
            return False

    async def _batch_processor(self, subscription: SubscriptionConfig):
        """Process messages in batches"""
        batch: List[tuple[Dict[str, Any], Dict[str, str]]] = []
        last_message_time = datetime.utcnow()

        while not self._stopping:
            try:
                # Get message from queue with timeout
                try:
                    message, headers = await asyncio.wait_for(
                        self._batch_queues[subscription.name].get(),
                        timeout=self.config.batch_timeout
                    )
                    batch.append((message, headers))
                    last_message_time = datetime.utcnow()
                except asyncio.TimeoutError:
                    pass

                # Process batch if full or timeout reached
                if (len(batch) >= self.config.batch_size or
                    (batch and (datetime.utcnow() - last_message_time).total_seconds() >= self.config.batch_timeout)):
                    
                    processor = self._processors[subscription.name]
                    messages = [m[0] for m in batch]
                    metadata = {
                        "batch_size": len(batch),
                        "subscription": subscription.name,
                        "timestamp": datetime.utcnow().isoformat()
                    }

                    try:
                        results = await processor.process_batch(messages, metadata)
                        
                        if self.metrics:
                            success_count = sum(1 for r in results if r)
                            await self.metrics.increment(
                                "subscriber.batch.processed",
                                tags={
                                    "subscription": subscription.name,
                                    "size": len(batch),
                                    "success_rate": success_count / len(batch)
                                }
                            )

                    except Exception as e:
                        if self.metrics:
                            await self.metrics.increment(
                                "subscriber.batch.failed",
                                tags={
                                    "subscription": subscription.name,
                                    "error": str(e)
                                }
                            )

                    batch = []

            except Exception as e:
                self.logger.error(f"Batch processing error: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight loop on error

    async def stop(self):
        """Stop all subscriptions"""
        self._stopping = True
        
        # Cancel all subscription tasks
        for task in self._active_subscriptions.values():
            task.cancel()
            
        # Wait for tasks to complete
        await asyncio.gather(
            *self._active_subscriptions.values(),
            return_exceptions=True
        )
        
        self._active_subscriptions.clear()
        self._batch_queues.clear() 