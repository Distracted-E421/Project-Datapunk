from typing import List, Dict, Any, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from ..queue.manager import QueueManager
from ...monitoring import MetricsCollector

T = TypeVar('T')

@dataclass
class BatchConfig:
    """Configuration for batch processing"""
    max_size: int = 100
    max_wait: float = 1.0  # seconds
    min_size: int = 1
    process_timeout: float = 30.0  # seconds
    retry_count: int = 3
    retry_delay: float = 1.0  # seconds
    enable_partial_batches: bool = True
    enable_ordered_processing: bool = False
    buffer_size: int = 1000

class BatchProcessor(Generic[T]):
    """Handles batch message processing"""
    def __init__(
        self,
        config: BatchConfig,
        queue_manager: QueueManager,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.queue_manager = queue_manager
        self.metrics = metrics_collector
        self._buffer = asyncio.Queue(maxsize=config.buffer_size)
        self._processing = False
        self._batch_task: Optional[asyncio.Task] = None
        self._current_batch: List[T] = []
        self._last_process_time = datetime.utcnow()
        self._batch_lock = asyncio.Lock()

    async def start(self):
        """Start batch processing"""
        if self._processing:
            return
        self._processing = True
        self._batch_task = asyncio.create_task(self._process_batches())

    async def stop(self):
        """Stop batch processing"""
        self._processing = False
        if self._batch_task:
            await self._batch_task
            self._batch_task = None

    async def add_item(self, item: T):
        """Add item to batch processing queue"""
        await self._buffer.put(item)

    async def _process_batches(self):
        """Main batch processing loop"""
        while self._processing:
            try:
                batch = await self._collect_batch()
                if batch:
                    await self._process_batch(batch)
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "batch.processing.error",
                        tags={"error": str(e)}
                    )
                # Sleep briefly to prevent tight loop on error
                await asyncio.sleep(0.1)

    async def _collect_batch(self) -> List[T]:
        """Collect items into a batch"""
        batch = []
        start_time = datetime.utcnow()

        while len(batch) < self.config.max_size:
            # Check if we've waited long enough
            if batch and (datetime.utcnow() - start_time).total_seconds() >= self.config.max_wait:
                break

            try:
                # Try to get an item with timeout
                item = await asyncio.wait_for(
                    self._buffer.get(),
                    timeout=max(0, self.config.max_wait - (datetime.utcnow() - start_time).total_seconds())
                )
                batch.append(item)
            except asyncio.TimeoutError:
                break

        # Return batch if it meets minimum size or partial batches are enabled
        if len(batch) >= self.config.min_size or (
            batch and self.config.enable_partial_batches
        ):
            return batch
        return []

    async def _process_batch(self, batch: List[T]):
        """Process a batch of items"""
        async with self._batch_lock:
            try:
                start_time = datetime.utcnow()
                
                # Process with timeout
                try:
                    await asyncio.wait_for(
                        self._handle_batch(batch),
                        timeout=self.config.process_timeout
                    )
                    
                    if self.metrics:
                        duration = (datetime.utcnow() - start_time).total_seconds()
                        await self.metrics.timing(
                            "batch.processing.duration",
                            duration,
                            tags={"size": len(batch)}
                        )
                        await self.metrics.increment(
                            "batch.processing.success",
                            tags={"size": len(batch)}
                        )
                        
                except asyncio.TimeoutError:
                    if self.metrics:
                        await self.metrics.increment(
                            "batch.processing.timeout",
                            tags={"size": len(batch)}
                        )
                    raise
                    
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "batch.processing.failure",
                        tags={"error": str(e), "size": len(batch)}
                    )
                # Handle failed batch
                await self._handle_failed_batch(batch, e)

    async def _handle_batch(self, batch: List[T]):
        """Override this method to implement batch processing logic"""
        raise NotImplementedError()

    async def _handle_failed_batch(self, batch: List[T], error: Exception):
        """Handle failed batch processing"""
        if len(batch) == 1 or not self.config.enable_partial_batches:
            # Single item or no partial processing - send to DLQ
            await self._send_to_dlq(batch, error)
            return

        # Split batch and retry smaller batches
        mid = len(batch) // 2
        await self._retry_batch(batch[:mid])
        await self._retry_batch(batch[mid:])

    async def _retry_batch(self, batch: List[T], retry_count: int = 0):
        """Retry processing a batch"""
        if retry_count >= self.config.retry_count:
            await self._send_to_dlq(batch, Exception("Max retries exceeded"))
            return

        # Add exponential backoff delay
        await asyncio.sleep(self.config.retry_delay * (2 ** retry_count))

        try:
            await self._process_batch(batch)
        except Exception as e:
            await self._retry_batch(batch, retry_count + 1)

    async def _send_to_dlq(self, batch: List[T], error: Exception):
        """Send failed items to Dead Letter Queue"""
        try:
            # Format DLQ message
            dlq_message = {
                "items": batch,
                "error": str(error),
                "timestamp": datetime.utcnow().isoformat(),
                "retry_count": self.config.retry_count
            }
            
            # Send to DLQ
            await self.queue_manager.publish(
                routing_key="dlq",
                message=dlq_message,
                headers={"error": str(error)}
            )
            
            if self.metrics:
                await self.metrics.increment(
                    "batch.dlq.sent",
                    tags={
                        "error": str(error),
                        "size": len(batch)
                    }
                )
                
        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "batch.dlq.error",
                    tags={"error": str(e)}
                ) 