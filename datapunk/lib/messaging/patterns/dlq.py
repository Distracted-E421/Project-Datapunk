"""
Dead Letter Queue (DLQ) module for Datapunk's messaging system.

Provides robust error handling and message recovery capabilities:
- Configurable retry policies with exponential backoff
- Message persistence with optional compression
- Automatic cleanup of expired messages
- Detailed metrics collection for monitoring and debugging

Designed to enhance system reliability by gracefully handling
message processing failures and providing mechanisms for recovery.
"""

from typing import Optional, Dict, Any, Generic, TypeVar, Callable
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from enum import Enum
import json
from ...monitoring import MetricsCollector

T = TypeVar('T')  # Message type
R = TypeVar('R')  # Result type

class FailureReason(Enum):
    """
    Categorizes reasons for message processing failures.
    
    Used to track and analyze different types of failures,
    enabling targeted debugging and system improvements.
    
    TODO: Consider adding more granular failure categories
    """
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    TIMEOUT = "timeout"
    DEPENDENCY_ERROR = "dependency_error"
    UNKNOWN = "unknown"

@dataclass
class DLQConfig:
    """
    Configuration for Dead Letter Queue behavior.
    
    Allows fine-tuning of DLQ parameters to balance between
    retry attempts, system load, and message expiration.
    
    NOTE: storage_path should be set for production environments
    FIXME: Consider adding support for external storage services
    """
    max_retries: int = 3
    retry_delay: float = 60.0  # seconds
    max_age: int = 7 * 24 * 60 * 60  # 7 days in seconds
    batch_size: int = 100
    enable_compression: bool = True
    compression_threshold: int = 1024  # bytes
    storage_path: Optional[str] = None
    cleanup_interval: int = 24 * 60 * 60  # 24 hours in seconds

@dataclass
class FailedMessage(Generic[T]):
    """
    Represents a message that failed processing.
    
    Stores all necessary information for retry attempts
    and failure analysis.
    
    NOTE: Ensure metadata doesn't contain sensitive information
    """
    id: str
    message: T
    reason: FailureReason
    error: str
    retry_count: int
    last_retry: datetime
    original_timestamp: datetime
    metadata: Dict[str, Any]

class DeadLetterQueue(Generic[T, R]):
    """
    Implements Dead Letter Queue pattern for handling failed messages.
    
    Features:
    - Configurable retry policies
    - Automatic message expiration and cleanup
    - Compression for efficient storage
    - Detailed metrics for monitoring and analysis
    
    TODO: Implement priority handling for critical messages
    TODO: Add support for external notification systems
    """
    
    async def start(self):
        """
        Initialize and start the DLQ processing.
        
        Loads persisted state (if any) and starts the cleanup task.
        
        NOTE: Ensure proper cleanup by calling stop() when shutting down
        """
        self._running = True
        if self.config.storage_path:
            await self._load_state()
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """
        Gracefully stop DLQ processing.
        
        Ensures all ongoing tasks are completed and state is persisted
        before shutting down.
        
        FIXME: Handle edge case where new messages arrive during shutdown
        """
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        if self.config.storage_path:
            await self._save_state()

    async def add_message(
        self,
        message_id: str,
        message: T,
        reason: FailureReason,
        error: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a failed message to the Dead Letter Queue.
        
        Stores the message with failure information and triggers
        metrics collection for monitoring.
        
        NOTE: Consider message size when setting compression threshold
        """
        async with self._lock:
            failed_message = FailedMessage(
                id=message_id,
                message=message,
                reason=reason,
                error=error,
                retry_count=0,
                last_retry=datetime.utcnow(),
                original_timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            self._messages[message_id] = failed_message
            
            if self.metrics:
                await self.metrics.increment(
                    "dlq.messages.added",
                    tags={
                        "reason": reason.value,
                        "error": error[:100]  # Truncate long errors
                    }
                )

    async def retry_message(self, message_id: str) -> bool:
        """
        Attempt to reprocess a failed message.
        
        Implements retry logic with exponential backoff and
        updates metrics based on the retry outcome.
        
        Returns True if processing succeeds, False otherwise.
        
        TODO: Implement circuit breaker pattern for repeated failures
        """
        async with self._lock:
            message = self._messages.get(message_id)
            if not message:
                return False

            try:
                # Process message
                result = await self.processor(message.message)
                
                # Remove from DLQ on success
                del self._messages[message_id]
                
                if self.metrics:
                    await self.metrics.increment(
                        "dlq.messages.retry_success",
                        tags={"reason": message.reason.value}
                    )
                
                return True

            except Exception as e:
                # Update retry count and timestamp
                message.retry_count += 1
                message.last_retry = datetime.utcnow()
                message.error = str(e)
                
                if self.metrics:
                    await self.metrics.increment(
                        "dlq.messages.retry_failed",
                        tags={
                            "reason": message.reason.value,
                            "error": str(e)[:100]
                        }
                    )
                
                return False

    async def retry_all(self, batch_size: Optional[int] = None) -> Dict[str, bool]:
        """
        Attempt to reprocess all eligible failed messages.
        
        Processes messages in batches to control system load.
        
        Returns a dictionary of message IDs and their processing outcomes.
        
        NOTE: Large numbers of retries may impact system performance
        """
        batch_size = batch_size or self.config.batch_size
        results = {}
        
        async with self._lock:
            eligible_messages = [
                msg_id for msg_id, msg in self._messages.items()
                if self._is_eligible_for_retry(msg)
            ][:batch_size]
            
            for message_id in eligible_messages:
                results[message_id] = await self.retry_message(message_id)
                
        return results

    def _is_eligible_for_retry(self, message: FailedMessage[T]) -> bool:
        """
        Determine if a message is eligible for retry.
        
        Checks against configured retry limits, delays, and message age
        to prevent unnecessary processing attempts.
        
        Returns True if the message should be retried, False otherwise.
        """
        now = datetime.utcnow()
        
        # Check max retries
        if message.retry_count >= self.config.max_retries:
            return False
            
        # Check retry delay
        if (now - message.last_retry).total_seconds() < self.config.retry_delay:
            return False
            
        # Check max age
        if (now - message.original_timestamp).total_seconds() > self.config.max_age:
            return False
            
        return True

    async def _cleanup_loop(self):
        """
        Periodically remove expired messages from the DLQ.
        
        Runs at configured intervals to prevent the DLQ from
        growing indefinitely with old, unprocessable messages.
        
        TODO: Implement adaptive cleanup intervals based on queue size
        """
        while self._running:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_expired_messages()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "dlq.cleanup.error",
                        tags={"error": str(e)}
                    )

    async def _cleanup_expired_messages(self):
        """
        Remove messages that have exceeded the maximum age.
        
        Prevents the DLQ from retaining messages indefinitely,
        which could lead to resource exhaustion.
        
        NOTE: Consider archiving expired messages for later analysis
        """
        now = datetime.utcnow()
        expired_ids = []
        
        async with self._lock:
            for message_id, message in self._messages.items():
                age = (now - message.original_timestamp).total_seconds()
                if age > self.config.max_age:
                    expired_ids.append(message_id)
                    
            for message_id in expired_ids:
                del self._messages[message_id]
                
            if self.metrics and expired_ids:
                await self.metrics.increment(
                    "dlq.messages.expired",
                    value=len(expired_ids)
                )

    async def _load_state(self):
        """Load DLQ state from storage"""
        if not self.config.storage_path:
            return

        try:
            with open(self.config.storage_path, 'r') as f:
                data = json.load(f)
                for msg_data in data:
                    msg_data["last_retry"] = datetime.fromisoformat(msg_data["last_retry"])
                    msg_data["original_timestamp"] = datetime.fromisoformat(
                        msg_data["original_timestamp"]
                    )
                    self._messages[msg_data["id"]] = FailedMessage(**msg_data)
                    
        except FileNotFoundError:
            pass
        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "dlq.storage.load_error",
                    tags={"error": str(e)}
                )

    async def _save_state(self):
        """Save DLQ state to storage"""
        if not self.config.storage_path:
            return

        try:
            with open(self.config.storage_path, 'w') as f:
                data = []
                for msg in self._messages.values():
                    msg_dict = vars(msg)
                    msg_dict["last_retry"] = msg_dict["last_retry"].isoformat()
                    msg_dict["original_timestamp"] = msg_dict["original_timestamp"].isoformat()
                    data.append(msg_dict)
                json.dump(data, f)
                
        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "dlq.storage.save_error",
                    tags={"error": str(e)}
                )

    async def get_stats(self) -> Dict[str, Any]:
        """Get DLQ statistics"""
        stats = {
            "total_messages": len(self._messages),
            "messages_by_reason": {},
            "retry_counts": {},
            "age_distribution": {
                "0_1h": 0,
                "1h_6h": 0,
                "6h_24h": 0,
                "24h_plus": 0
            }
        }
        
        now = datetime.utcnow()
        
        for message in self._messages.values():
            # Count by reason
            reason = message.reason.value
            stats["messages_by_reason"][reason] = (
                stats["messages_by_reason"].get(reason, 0) + 1
            )
            
            # Count by retry count
            retry_count = str(message.retry_count)
            stats["retry_counts"][retry_count] = (
                stats["retry_counts"].get(retry_count, 0) + 1
            )
            
            # Count by age
            age_hours = (now - message.original_timestamp).total_seconds() / 3600
            if age_hours <= 1:
                stats["age_distribution"]["0_1h"] += 1
            elif age_hours <= 6:
                stats["age_distribution"]["1h_6h"] += 1
            elif age_hours <= 24:
                stats["age_distribution"]["6h_24h"] += 1
            else:
                stats["age_distribution"]["24h_plus"] += 1
                
        return stats 