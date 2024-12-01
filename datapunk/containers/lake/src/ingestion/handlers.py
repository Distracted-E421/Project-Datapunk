from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass, field
import json
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_second: float
    burst_size: int
    window_size: timedelta = timedelta(seconds=1)
    
class TokenBucket:
    """Token bucket algorithm implementation for rate limiting"""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = datetime.utcnow()
        self._lock = asyncio.Lock()
        
    async def acquire(self, tokens: int = 1) -> bool:
        """Attempt to acquire tokens from the bucket"""
        async with self._lock:
            now = datetime.utcnow()
            time_passed = (now - self.last_update).total_seconds()
            self.tokens = min(
                self.capacity,
                self.tokens + time_passed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

class RateLimiter:
    """Rate limiter for ingestion requests"""
    
    def __init__(self, config: RateLimitConfig):
        self.bucket = TokenBucket(config.requests_per_second, config.burst_size)
        self.config = config
        
    async def check_limit(self, tokens: int = 1) -> bool:
        """Check if request is within rate limits"""
        return await self.bucket.acquire(tokens)
        
    async def wait_for_capacity(self, tokens: int = 1, timeout: float = None) -> bool:
        """Wait for rate limit capacity to become available"""
        start_time = datetime.utcnow()
        while True:
            if await self.check_limit(tokens):
                return True
                
            if timeout:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed >= timeout:
                    return False
                    
            await asyncio.sleep(0.1)  # Prevent tight loop

@dataclass
class ErrorContext:
    """Context information for error handling"""
    error_type: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    traceback: Optional[str] = None

class ErrorHandler:
    """Error handler for ingestion pipeline"""
    
    def __init__(self):
        self._error_handlers: Dict[str, List[callable]] = {}
        self._error_queue: asyncio.Queue = asyncio.Queue()
        self._is_running = False
        
    async def start(self):
        """Start the error handling process"""
        if self._is_running:
            return
            
        self._is_running = True
        asyncio.create_task(self._process_errors())
        
    async def stop(self):
        """Stop the error handling process"""
        self._is_running = False
        
    async def register_handler(self, error_type: str, handler: callable):
        """Register a handler for a specific error type"""
        if error_type not in self._error_handlers:
            self._error_handlers[error_type] = []
        self._error_handlers[error_type].append(handler)
        
    async def handle_error(self, context: ErrorContext):
        """Handle an error with the registered handlers"""
        await self._error_queue.put(context)
        
    async def _process_errors(self):
        """Process errors from the queue"""
        while self._is_running:
            try:
                context = await self._error_queue.get()
                handlers = self._error_handlers.get(context.error_type, [])
                
                if not handlers:
                    # Default error handling if no specific handlers
                    logger.error(
                        f"Unhandled error: {context.error_type} - {context.message}",
                        extra={"context": context}
                    )
                    continue
                    
                for handler in handlers:
                    try:
                        await handler(context)
                    except Exception as e:
                        logger.error(
                            f"Error handler failed: {str(e)}",
                            extra={"handler": handler, "context": context}
                        )
                        
            except Exception as e:
                logger.error(f"Error processing error queue: {str(e)}")
            finally:
                self._error_queue.task_done()

class RetryStrategy(ABC):
    """Base class for retry strategies"""
    
    @abstractmethod
    async def should_retry(self, attempt: int, error: Exception) -> bool:
        """Determine if another retry attempt should be made"""
        pass
        
    @abstractmethod
    async def get_delay(self, attempt: int) -> float:
        """Get the delay before the next retry attempt"""
        pass

class ExponentialBackoff(RetryStrategy):
    """Exponential backoff retry strategy"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        
    async def should_retry(self, attempt: int, error: Exception) -> bool:
        """Check if retry should be attempted based on attempt count and error type"""
        if attempt >= self.max_attempts:
            return False
            
        # Add specific error type checks here
        return isinstance(error, (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError
        ))
        
    async def get_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff"""
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        return min(delay, self.max_delay)

class RetryHandler:
    """Handles retry logic for failed operations"""
    
    def __init__(self, strategy: RetryStrategy):
        self.strategy = strategy
        
    async def execute_with_retry(
        self,
        operation: callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute an operation with retry logic"""
        attempt = 1
        last_error = None
        
        while True:
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                if not await self.strategy.should_retry(attempt, e):
                    raise last_error
                    
                delay = await self.strategy.get_delay(attempt)
                logger.warning(
                    f"Retry attempt {attempt} failed: {str(e)}. "
                    f"Retrying in {delay} seconds..."
                )
                
                await asyncio.sleep(delay)
                attempt += 1 