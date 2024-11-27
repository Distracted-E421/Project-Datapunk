from typing import Optional, Dict, Any, List, Generic, TypeVar, Callable, Union
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from enum import Enum
import json
from ..patterns.retry import RetryPolicy
from ..patterns.dlq import DeadLetterQueue, FailureReason
from ..patterns.batch import BatchProcessor
from ...monitoring import MetricsCollector

T = TypeVar('T')  # Message type
R = TypeVar('R')  # Result type

"""
Queue Management System for Datapunk's Messaging Infrastructure

A flexible queue management system supporting multiple queue types and processing patterns.
Designed to handle various messaging scenarios while maintaining reliability and performance.

Key Features:
- Multiple queue types (FIFO, Priority, Delay, Batch, Topic)
- Message persistence and compression
- Dead letter queue integration
- Retry policy support
- Metrics collection

Design Philosophy:
- Prioritizes message reliability over raw performance
- Supports both synchronous and asynchronous processing
- Implements backpressure through queue size limits
- Provides comprehensive monitoring capabilities

NOTE: This implementation assumes single-process usage
TODO: Add support for distributed queue management
"""

class QueueType(Enum):
    """
    Supported queue types with different message handling characteristics.
    
    Why These Types:
    FIFO: Ensures strict message ordering
    PRIORITY: Handles urgent messages first
    DELAY: Supports scheduled message processing
    BATCH: Optimizes throughput for high volume
    TOPIC: Enables pub/sub message routing
    """
    FIFO = "fifo"           # First In First Out
    PRIORITY = "priority"   # Priority-based
    DELAY = "delay"        # Delayed delivery
    BATCH = "batch"        # Batch processing
    TOPIC = "topic"        # Topic-based routing

@dataclass
class QueueConfig:
    """
    Queue behavior configuration.
    
    Design Considerations:
    - max_size prevents memory exhaustion
    - compression_threshold balances CPU vs memory usage
    - cleanup_interval manages memory usage over time
    
    WARNING: Setting batch_size too high may cause processing delays
    TODO: Add validation for interdependent parameters
    """
    queue_type: QueueType = QueueType.FIFO
    max_size: int = 10000
    enable_persistence: bool = True
    storage_path: Optional[str] = None
    enable_compression: bool = True
    compression_threshold: int = 1024  # bytes
    batch_size: int = 100
    batch_timeout: float = 5.0  # seconds
    max_priority: int = 10
    default_priority: int = 5
    max_delay: int = 3600  # seconds
    cleanup_interval: int = 3600  # seconds
    enable_dlq: bool = True
    enable_retry: bool = True

class QueueMessage(Generic[T]):
    """
    Message container with metadata for queue management.
    
    Features:
    - Unique message identification
    - Priority support
    - Delayed processing capability
    - Attempt tracking for retry logic
    
    NOTE: metadata dict can be used for custom routing/processing logic
    """
    def __init__(
        self,
        id: str,
        payload: T,
        priority: int = 0,
        delay_until: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id
        self.payload = payload
        self.priority = priority
        self.delay_until = delay_until
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.attempts = 0

class QueueManager(Generic[T, R]):
    """
    Manages message queues with configurable processing behavior.
    
    Key Capabilities:
    - Multiple queue type support
    - Message persistence
    - Batch processing
    - Retry handling
    - Dead letter queue integration
    
    FIXME: Consider adding queue partitioning for better scaling
    """
    def __init__(
        self,
        config: QueueConfig,
        processor: Callable[[T], R],
        retry_policy: Optional[RetryPolicy] = None,
        dlq: Optional[DeadLetterQueue] = None,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.processor = processor
        self.retry_policy = retry_policy
        self.dlq = dlq
        self.metrics = metrics_collector
        self._queues: Dict[str, List[QueueMessage[T]]] = {}
        self._batch_processor: Optional[BatchProcessor] = None
        self._processing_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()

    async def start(self):
        """
        Initializes queue processing and maintenance tasks.
        
        Implementation Notes:
        - Loads persisted state if enabled
        - Starts batch processor if configured
        - Initializes cleanup task
        
        WARNING: Ensure proper cleanup by calling stop() when done
        """
        self._running = True
        if self.config.enable_persistence:
            await self._load_state()

        if self.config.queue_type == QueueType.BATCH:
            self._batch_processor = BatchProcessor(
                batch_size=self.config.batch_size,
                batch_timeout=self.config.batch_timeout,
                processor=self.processor,
                metrics_collector=self.metrics
            )
            await self._batch_processor.start()

        self._processing_task = asyncio.create_task(self._processing_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop queue processing"""
        self._running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self._batch_processor:
            await self._batch_processor.stop()

        if self.config.enable_persistence:
            await self._save_state()

    async def enqueue(
        self,
        queue_name: str,
        message: T,
        priority: Optional[int] = None,
        delay: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Adds message to specified queue with optional parameters.
        
        Design Decisions:
        - Uses lock for thread safety
        - Implements queue size limits
        - Supports priority insertion
        - Handles delayed messages
        
        NOTE: Priority ordering only applies to PRIORITY queue type
        """
        async with self._lock:
            # Create queue if it doesn't exist
            if queue_name not in self._queues:
                self._queues[queue_name] = []

            # Check queue size limit
            if len(self._queues[queue_name]) >= self.config.max_size:
                if self.metrics:
                    await self.metrics.increment(
                        "queue.enqueue.rejected",
                        tags={"queue": queue_name, "reason": "full"}
                    )
                raise QueueFullError(f"Queue {queue_name} is full")

            # Create message
            msg = QueueMessage(
                id=f"{queue_name}_{len(self._queues[queue_name])}",
                payload=message,
                priority=min(
                    priority or self.config.default_priority,
                    self.config.max_priority
                ),
                delay_until=(
                    datetime.utcnow() + timedelta(seconds=delay)
                    if delay else None
                ),
                metadata=metadata
            )

            # Add to queue
            if self.config.queue_type == QueueType.PRIORITY:
                # Insert maintaining priority order
                insert_idx = 0
                for i, existing_msg in enumerate(self._queues[queue_name]):
                    if msg.priority > existing_msg.priority:
                        insert_idx = i
                        break
                self._queues[queue_name].insert(insert_idx, msg)
            else:
                self._queues[queue_name].append(msg)

            if self.metrics:
                await self.metrics.increment(
                    "queue.message.enqueued",
                    tags={"queue": queue_name}
                )

            return msg.id

    async def dequeue(
        self,
        queue_name: str,
        batch_size: Optional[int] = None
    ) -> Union[Optional[QueueMessage[T]], List[QueueMessage[T]]]:
        """Get message(s) from queue"""
        async with self._lock:
            if queue_name not in self._queues:
                return [] if batch_size else None

            now = datetime.utcnow()
            available_messages = [
                msg for msg in self._queues[queue_name]
                if not msg.delay_until or now >= msg.delay_until
            ]

            if not available_messages:
                return [] if batch_size else None

            if batch_size:
                # Return batch of messages
                messages = available_messages[:batch_size]
                self._queues[queue_name] = [
                    msg for msg in self._queues[queue_name]
                    if msg not in messages
                ]
                return messages
            else:
                # Return single message
                message = available_messages[0]
                self._queues[queue_name].remove(message)
                return message

    async def _processing_loop(self):
        """Main message processing loop"""
        while self._running:
            try:
                for queue_name in list(self._queues.keys()):
                    if self.config.queue_type == QueueType.BATCH:
                        await self._process_batch(queue_name)
                    else:
                        await self._process_message(queue_name)

                await asyncio.sleep(0.1)  # Prevent busy loop

            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "queue.processing.error",
                        tags={"error": str(e)}
                    )

    async def _process_message(self, queue_name: str):
        """
        Processes single message with retry and DLQ handling.
        
        Error Handling Strategy:
        - Tracks attempt count
        - Applies retry policy if configured
        - Moves to DLQ after max retries
        - Records metrics for monitoring
        
        TODO: Add support for custom error handlers
        """
        message = await self.dequeue(queue_name)
        if not message:
            return

        try:
            if self.retry_policy:
                processor = self.retry_policy.wrap(self.processor)
            else:
                processor = self.processor

            result = await processor(message.payload)

            if self.metrics:
                await self.metrics.increment(
                    "queue.message.processed",
                    tags={"queue": queue_name}
                )

            return result

        except Exception as e:
            message.attempts += 1
            if self.dlq and message.attempts >= self.config.max_retries:
                await self.dlq.add_message(
                    message_id=message.id,
                    message=message.payload,
                    reason=FailureReason.PROCESSING_ERROR,
                    error=str(e),
                    metadata={
                        "queue": queue_name,
                        "attempts": message.attempts,
                        **message.metadata
                    }
                )

            if self.metrics:
                await self.metrics.increment(
                    "queue.processing.error",
                    tags={
                        "queue": queue_name,
                        "error": str(e)
                    }
                )

    async def _process_batch(self, queue_name: str):
        """Process batch of messages"""
        messages = await self.dequeue(
            queue_name,
            batch_size=self.config.batch_size
        )
        if not messages:
            return

        try:
            results = await self._batch_processor.process_batch(
                [msg.payload for msg in messages]
            )

            if self.metrics:
                await self.metrics.increment(
                    "queue.batch.processed",
                    tags={
                        "queue": queue_name,
                        "size": len(messages)
                    }
                )

            return results

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "queue.batch.error",
                    tags={
                        "queue": queue_name,
                        "error": str(e)
                    }
                )

            # Handle failed messages
            for message in messages:
                message.attempts += 1
                if self.dlq and message.attempts >= self.config.max_retries:
                    await self.dlq.add_message(
                        message_id=message.id,
                        message=message.payload,
                        reason=FailureReason.PROCESSING_ERROR,
                        error=str(e),
                        metadata={
                            "queue": queue_name,
                            "batch": True,
                            "attempts": message.attempts,
                            **message.metadata
                        }
                    )

    async def _cleanup_loop(self):
        """Periodic cleanup of processed messages"""
        while self._running:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_queues()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "queue.cleanup.error",
                        tags={"error": str(e)}
                    )

    async def _cleanup_queues(self):
        """
        Performs periodic queue maintenance.
        
        Maintenance Tasks:
        - Removes processed messages
        - Manages memory usage
        - Updates metrics
        
        NOTE: Consider implementing more aggressive cleanup for high-volume queues
        """
        async with self._lock:
            for queue_name in self._queues:
                # Remove processed messages
                self._queues[queue_name] = [
                    msg for msg in self._queues[queue_name]
                    if not msg.processed
                ]

    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            "queues": len(self._queues),
            "messages": {},
            "type": self.config.queue_type.value
        }

        for queue_name, messages in self._queues.items():
            stats["messages"][queue_name] = {
                "total": len(messages),
                "delayed": sum(
                    1 for m in messages
                    if m.delay_until and m.delay_until > datetime.utcnow()
                ),
                "by_priority": {
                    i: sum(1 for m in messages if m.priority == i)
                    for i in range(self.config.max_priority + 1)
                }
            }

        return stats

class QueueFullError(Exception):
    """Error when queue is full"""
    pass 