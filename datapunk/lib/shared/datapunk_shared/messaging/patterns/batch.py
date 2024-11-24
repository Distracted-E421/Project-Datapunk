from typing import Optional, Dict, Any, List, Generic, TypeVar, Callable
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from ...monitoring import MetricsCollector

T = TypeVar('T')  # Type of message
R = TypeVar('R')  # Type of result

class BatchTrigger(Enum):
    """Batch processing triggers"""
    SIZE = "size"           # Trigger on batch size
    TIMEOUT = "timeout"     # Trigger on time elapsed
    BOTH = "both"          # Trigger on either condition
    ALL = "all"            # Trigger when both conditions met

@dataclass
class BatchConfig:
    """Configuration for batch processing"""
    max_size: int = 100  # Maximum batch size
    max_wait: float = 5.0  # Maximum wait time in seconds
    trigger: BatchTrigger = BatchTrigger.BOTH
    retry_failed: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    enable_partial_batches: bool = True
    enable_parallel_processing: bool = True
    max_concurrent_batches: int = 5
    compression_threshold: int = 1024  # bytes

class BatchProcessor(Generic[T, R]):
    """Handles batch processing of messages"""
    def __init__(
        self,
        config: BatchConfig,
        processor: Callable[[List[T]], List[R]],
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.processor = processor
        self.metrics = metrics_collector
        self._current_batch: List[T] = []
        self._batch_start: Optional[datetime] = None
        self._processing = False
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(config.max_concurrent_batches)
        self._batch_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start batch processor"""
        self._processing = True
        self._batch_task = asyncio.create_task(self._batch_loop())

    async def stop(self):
        """Stop batch processor"""
        self._processing = False
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass
            # Process any remaining messages
            if self._current_batch:
                await self._process_batch(self._current_batch)

    async def add_message(self, message: T):
        """Add message to current batch"""
        async with self._lock:
            if not self._batch_start:
                self._batch_start = datetime.utcnow()

            self._current_batch.append(message)

            if self._should_process_batch():
                await self._process_current_batch()

    async def _batch_loop(self):
        """Main batch processing loop"""
        while self._processing:
            try:
                if self._batch_start:
                    elapsed = (datetime.utcnow() - self._batch_start).total_seconds()
                    if elapsed >= self.config.max_wait:
                        async with self._lock:
                            if self._current_batch:  # Check again under lock
                                await self._process_current_batch()
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy loop
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "batch.loop.error",
                        tags={"error": str(e)}
                    )

    def _should_process_batch(self) -> bool:
        """Check if batch should be processed"""
        if not self._current_batch:
            return False

        size_trigger = len(self._current_batch) >= self.config.max_size
        time_trigger = False
        
        if self._batch_start:
            elapsed = (datetime.utcnow() - self._batch_start).total_seconds()
            time_trigger = elapsed >= self.config.max_wait

        if self.config.trigger == BatchTrigger.SIZE:
            return size_trigger
        elif self.config.trigger == BatchTrigger.TIMEOUT:
            return time_trigger
        elif self.config.trigger == BatchTrigger.BOTH:
            return size_trigger or time_trigger
        else:  # BatchTrigger.ALL
            return size_trigger and time_trigger

    async def _process_current_batch(self):
        """Process current batch of messages"""
        batch = self._current_batch
        self._current_batch = []
        self._batch_start = None
        
        if batch:  # Double check we have messages
            await self._process_batch(batch)

    async def _process_batch(self, batch: List[T]):
        """Process a batch of messages"""
        if not batch:
            return

        async with self._semaphore:
            start_time = datetime.utcnow()
            retries = 0
            
            while retries <= self.config.max_retries:
                try:
                    # Process batch
                    results = await asyncio.get_event_loop().run_in_executor(
                        None, self.processor, batch
                    )
                    
                    duration = (datetime.utcnow() - start_time).total_seconds()
                    
                    if self.metrics:
                        await self.metrics.timing(
                            "batch.processing.duration",
                            duration,
                            tags={
                                "size": len(batch),
                                "retries": retries
                            }
                        )
                        await self.metrics.increment(
                            "batch.processing.success",
                            tags={"size": len(batch)}
                        )
                    
                    return results

                except Exception as e:
                    retries += 1
                    
                    if self.metrics:
                        await self.metrics.increment(
                            "batch.processing.error",
                            tags={
                                "error": str(e),
                                "retry": retries
                            }
                        )
                    
                    if retries > self.config.max_retries:
                        if self.config.enable_partial_batches and len(batch) > 1:
                            # Split batch and retry
                            mid = len(batch) // 2
                            await self._process_batch(batch[:mid])
                            await self._process_batch(batch[mid:])
                            return
                        raise  # Re-raise the last error
                        
                    # Wait before retry
                    await asyncio.sleep(
                        self.config.retry_delay * (2 ** (retries - 1))
                    )

    def _compress_batch(self, batch: List[T]) -> bytes:
        """Compress batch data if it exceeds threshold"""
        data = self._serialize_batch(batch)
        if len(data) > self.config.compression_threshold:
            import zlib
            return zlib.compress(data)
        return data

    def _decompress_batch(self, data: bytes) -> List[T]:
        """Decompress batch data"""
        try:
            import zlib
            data = zlib.decompress(data)
        except zlib.error:
            pass  # Data wasn't compressed
        return self._deserialize_batch(data)

    def _serialize_batch(self, batch: List[T]) -> bytes:
        """Serialize batch for storage/transmission"""
        import pickle
        return pickle.dumps(batch)

    def _deserialize_batch(self, data: bytes) -> List[T]:
        """Deserialize batch from storage/transmission"""
        import pickle
        return pickle.loads(data)

    async def get_stats(self) -> Dict[str, Any]:
        """Get batch processor statistics"""
        return {
            "current_batch_size": len(self._current_batch),
            "batch_age": (
                (datetime.utcnow() - self._batch_start).total_seconds()
                if self._batch_start else 0
            ),
            "is_processing": self._processing,
            "config": {
                "max_size": self.config.max_size,
                "max_wait": self.config.max_wait,
                "trigger": self.config.trigger.value,
                "max_retries": self.config.max_retries
            }
        } 