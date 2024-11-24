from typing import Optional, Dict, Any, Callable, Generic, TypeVar, List
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from ..patterns.retry import RetryPolicy
from ..patterns.batch import BatchProcessor
from ...monitoring import MetricsCollector

T = TypeVar('T')  # Message type
R = TypeVar('R')  # Result type

class SubscriptionMode(Enum):
    """Subscription processing modes"""
    INDIVIDUAL = "individual"  # Process messages individually
    BATCH = "batch"           # Process messages in batches
    STREAMING = "streaming"   # Stream messages continuously

@dataclass
class SubscriptionConfig:
    """Configuration for message subscription"""
    mode: SubscriptionMode = SubscriptionMode.INDIVIDUAL
    batch_size: int = 100
    batch_timeout: float = 5.0  # seconds
    max_concurrent: int = 10
    prefetch_count: int = 1000
    enable_auto_ack: bool = False
    ack_timeout: float = 30.0  # seconds
    enable_retry: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    dead_letter_topic: Optional[str] = None

class MessageSubscriber(Generic[T, R]):
    """Handles message subscription and processing"""
    def __init__(
        self,
        config: SubscriptionConfig,
        processor: Callable[[T], R],
        retry_policy: Optional[RetryPolicy] = None,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.processor = processor
        self.retry_policy = retry_policy
        self.metrics = metrics_collector
        self._batch_processor: Optional[BatchProcessor] = None
        self._processing_tasks: List[asyncio.Task] = []
        self._unacked_messages: Dict[str, datetime] = {}
        self._running = False
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(config.max_concurrent)

    async def start(self):
        """Start subscriber processing"""
        self._running = True
        
        if self.config.mode == SubscriptionMode.BATCH:
            self._batch_processor = BatchProcessor(
                batch_size=self.config.batch_size,
                batch_timeout=self.config.batch_timeout,
                processor=self.processor,
                metrics_collector=self.metrics
            )
            await self._batch_processor.start()

        # Start ack timeout checker if auto-ack is disabled
        if not self.config.enable_auto_ack:
            self._processing_tasks.append(
                asyncio.create_task(self._check_ack_timeouts())
            )

    async def stop(self):
        """Stop subscriber processing"""
        self._running = False
        
        if self._batch_processor:
            await self._batch_processor.stop()

        # Cancel all processing tasks
        for task in self._processing_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._processing_tasks.clear()

    async def process_message(
        self,
        message_id: str,
        message: T
    ) -> Optional[R]:
        """Process a single message"""
        async with self._semaphore:
            try:
                if not self.config.enable_auto_ack:
                    self._unacked_messages[message_id] = datetime.utcnow()

                if self.config.mode == SubscriptionMode.BATCH:
                    await self._batch_processor.add_message(message)
                    result = None
                else:
                    # Process individual message
                    processor = self.processor
                    if self.config.enable_retry and self.retry_policy:
                        processor = self.retry_policy.wrap(processor)

                    result = await processor(message)

                if self.config.enable_auto_ack:
                    await self.ack_message(message_id)

                if self.metrics:
                    await self.metrics.increment(
                        "subscriber.message.processed",
                        tags={"mode": self.config.mode.value}
                    )

                return result

            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "subscriber.message.error",
                        tags={
                            "mode": self.config.mode.value,
                            "error": str(e)
                        }
                    )
                raise

    async def ack_message(self, message_id: str):
        """Acknowledge message processing"""
        async with self._lock:
            self._unacked_messages.pop(message_id, None)
            
            if self.metrics:
                await self.metrics.increment("subscriber.message.acked")

    async def nack_message(
        self,
        message_id: str,
        requeue: bool = True
    ):
        """Negative acknowledge message processing"""
        async with self._lock:
            self._unacked_messages.pop(message_id, None)
            
            if self.metrics:
                await self.metrics.increment(
                    "subscriber.message.nacked",
                    tags={"requeue": str(requeue)}
                )

    async def _check_ack_timeouts(self):
        """Check for message acknowledgement timeouts"""
        while self._running:
            try:
                await asyncio.sleep(1.0)  # Check every second
                await self._process_timeouts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "subscriber.timeout_check.error",
                        tags={"error": str(e)}
                    )

    async def _process_timeouts(self):
        """Process timed out messages"""
        now = datetime.utcnow()
        timeout_threshold = now - timedelta(seconds=self.config.ack_timeout)
        
        async with self._lock:
            timed_out = [
                msg_id for msg_id, timestamp in self._unacked_messages.items()
                if timestamp <= timeout_threshold
            ]
            
            for message_id in timed_out:
                await self.nack_message(message_id)
                
                if self.metrics:
                    await self.metrics.increment("subscriber.message.timeout")

    async def get_stats(self) -> Dict[str, Any]:
        """Get subscriber statistics"""
        stats = {
            "mode": self.config.mode.value,
            "unacked_messages": len(self._unacked_messages),
            "processing_tasks": len(self._processing_tasks),
            "is_running": self._running
        }
        
        if self._batch_processor:
            stats["batch_processor"] = await self._batch_processor.get_stats()
            
        return stats 