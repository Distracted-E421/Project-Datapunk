from typing import Optional, Dict, Any, Callable, List, TypeVar, Generic
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from ..queue.manager import QueueManager
from .retry import RetryHandler, RetryConfig, RetryStrategy
from ...monitoring import MetricsCollector

T = TypeVar('T')

@dataclass
class DLQConfig:
    """Configuration for Dead Letter Queue"""
    queue_name: str
    max_retries: int = 3
    retry_delay: float = 60.0  # seconds
    cleanup_interval: int = 24 * 60 * 60  # 24 hours in seconds
    message_ttl: int = 7 * 24 * 60 * 60  # 7 days in seconds
    batch_size: int = 10
    enable_auto_retry: bool = True
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    enable_archiving: bool = True
    archive_after_days: int = 30

class DLQHandler(Generic[T]):
    """Handles Dead Letter Queue operations"""
    def __init__(
        self,
        config: DLQConfig,
        queue_manager: QueueManager,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.queue_manager = queue_manager
        self.metrics = metrics_collector
        self._retry_handler = RetryHandler(
            RetryConfig(
                max_attempts=config.max_retries,
                initial_delay=config.retry_delay,
                strategy=config.retry_strategy
            ),
            metrics_collector
        )
        self._cleanup_task: Optional[asyncio.Task] = None
        self._retry_task: Optional[asyncio.Task] = None
        self._processing = False

    async def start(self):
        """Start DLQ processing"""
        self._processing = True
        if self.config.enable_auto_retry:
            self._retry_task = asyncio.create_task(self._auto_retry_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop DLQ processing"""
        self._processing = False
        if self._retry_task:
            self._retry_task.cancel()
            try:
                await self._retry_task
            except asyncio.CancelledError:
                pass
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def handle_failed_message(
        self,
        message: T,
        error: Exception,
        original_queue: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Handle a failed message by moving it to DLQ"""
        try:
            dlq_message = {
                "message": message,
                "error": str(error),
                "original_queue": original_queue,
                "timestamp": datetime.utcnow().isoformat(),
                "retry_count": 0,
                "metadata": metadata or {}
            }

            await self.queue_manager.publish(
                routing_key=self.config.queue_name,
                message=dlq_message,
                headers={
                    "x-original-queue": original_queue,
                    "x-error": str(error),
                    "x-first-failure": datetime.utcnow().isoformat()
                }
            )

            if self.metrics:
                await self.metrics.increment(
                    "dlq.messages.added",
                    tags={
                        "queue": original_queue,
                        "error": error.__class__.__name__
                    }
                )

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "dlq.handle.error",
                    tags={"error": str(e)}
                )
            raise

    async def retry_message(
        self,
        message_id: str,
        handler: Callable[[T], Any]
    ) -> bool:
        """Retry a specific message from DLQ"""
        try:
            # Get message from DLQ
            message = await self.queue_manager.get_message(
                self.config.queue_name,
                message_id
            )

            if not message:
                return False

            # Attempt to process with retry handler
            success = await self._retry_handler.execute(
                handler,
                message["message"]
            )

            if success:
                # Remove from DLQ on success
                await self.queue_manager.ack_message(
                    self.config.queue_name,
                    message_id
                )

                if self.metrics:
                    await self.metrics.increment(
                        "dlq.messages.retried.success",
                        tags={"queue": message["original_queue"]}
                    )

            return success

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "dlq.retry.error",
                    tags={"error": str(e)}
                )
            return False

    async def _auto_retry_loop(self):
        """Automatic retry loop for DLQ messages"""
        while self._processing:
            try:
                # Get batch of messages from DLQ
                messages = await self.queue_manager.get_messages(
                    self.config.queue_name,
                    batch_size=self.config.batch_size
                )

                for message in messages:
                    retry_count = message.get("retry_count", 0)
                    if retry_count < self.config.max_retries:
                        # Attempt retry
                        try:
                            await self.queue_manager.publish(
                                routing_key=message["original_queue"],
                                message=message["message"]
                            )
                            
                            # Update retry count
                            message["retry_count"] = retry_count + 1
                            await self.queue_manager.update_message(
                                self.config.queue_name,
                                message["id"],
                                message
                            )

                            if self.metrics:
                                await self.metrics.increment(
                                    "dlq.messages.auto_retried",
                                    tags={
                                        "queue": message["original_queue"],
                                        "attempt": retry_count + 1
                                    }
                                )

                        except Exception as e:
                            if self.metrics:
                                await self.metrics.increment(
                                    "dlq.auto_retry.error",
                                    tags={"error": str(e)}
                                )

                await asyncio.sleep(self.config.retry_delay)

            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "dlq.auto_retry_loop.error",
                        tags={"error": str(e)}
                    )
                await asyncio.sleep(self.config.retry_delay)

    async def _cleanup_loop(self):
        """Cleanup loop for old DLQ messages"""
        while self._processing:
            try:
                cutoff_time = datetime.utcnow() - timedelta(
                    seconds=self.config.message_ttl
                )

                # Get expired messages
                expired_messages = await self.queue_manager.get_messages(
                    self.config.queue_name,
                    filter_fn=lambda m: (
                        datetime.fromisoformat(m["timestamp"]) < cutoff_time
                    )
                )

                for message in expired_messages:
                    if self.config.enable_archiving:
                        # Archive message before removal
                        await self._archive_message(message)

                    # Remove from DLQ
                    await self.queue_manager.delete_message(
                        self.config.queue_name,
                        message["id"]
                    )

                    if self.metrics:
                        await self.metrics.increment(
                            "dlq.messages.cleaned",
                            tags={"queue": message["original_queue"]}
                        )

                await asyncio.sleep(self.config.cleanup_interval)

            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "dlq.cleanup_loop.error",
                        tags={"error": str(e)}
                    )
                await asyncio.sleep(self.config.cleanup_interval)

    async def _archive_message(self, message: Dict[str, Any]):
        """Archive a DLQ message"""
        try:
            archive_message = {
                **message,
                "archived_at": datetime.utcnow().isoformat()
            }

            await self.queue_manager.publish(
                routing_key=f"{self.config.queue_name}.archive",
                message=archive_message
            )

            if self.metrics:
                await self.metrics.increment(
                    "dlq.messages.archived",
                    tags={"queue": message["original_queue"]}
                )

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "dlq.archive.error",
                    tags={"error": str(e)}
                ) 