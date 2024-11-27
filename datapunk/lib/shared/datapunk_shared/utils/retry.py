"""
Retry Utility for Datapunk's Distributed Operations

Implements an intelligent retry mechanism for handling transient failures
in distributed systems. Uses exponential backoff with jitter to prevent
thundering herd problems in service recovery scenarios.

Key features:
- Configurable retry attempts and delays
- Exponential backoff with randomized jitter
- Structured logging of retry attempts
- Exception-specific retry policies

Usage in service mesh:
- Network operation retries
- Database connection recovery
- Message queue operations
- Service discovery refreshes

NOTE: This is a critical reliability component used throughout the system.
Changes should be carefully considered as they affect overall system resilience.
"""

from typing import Type, Tuple, Callable, Any
import asyncio
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class RetryConfig:
    """
    Configuration for retry behavior.
    
    Implements exponential backoff with jitter to prevent synchronized
    retry storms in distributed systems. Default values are chosen to
    balance quick recovery with system stability.
    
    NOTE: These defaults should be tuned based on specific service SLAs
    and failure recovery requirements.
    """
    max_attempts: int = 3  # Balance between persistence and fail-fast
    base_delay: float = 1.0  # Initial delay between attempts
    max_delay: float = 30.0  # Cap on exponential growth
    exponential: bool = True  # Use exponential backoff
    jitter: bool = True  # Add randomization to prevent synchronized retries

def with_retry(
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    config: RetryConfig = None
):
    """
    Decorator implementing retry logic with exponential backoff.
    
    Designed for distributed system resilience:
    - Handles transient failures gracefully
    - Prevents cascading failures through backoff
    - Provides visibility through structured logging
    
    TODO: Add circuit breaker integration
    TODO: Implement retry budgets for system-wide retry management
    
    Args:
        exceptions: Tuple of exceptions to retry on
        config: RetryConfig instance (uses defaults if None)
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            last_exception = None

            while attempt < config.max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    last_exception = e

                    if attempt == config.max_attempts:
                        # Log final failure with full context for debugging
                        logger.error(
                            "Max retry attempts reached",
                            function=func.__name__,
                            attempt=attempt,
                            error=str(e)
                        )
                        raise

                    # Calculate delay with exponential backoff and jitter
                    # FIXME: Consider moving delay calculation to separate method
                    delay = config.base_delay
                    if config.exponential:
                        delay *= (2 ** (attempt - 1))  # Exponential growth
                    if config.jitter:
                        # Add up to 10% random jitter to prevent thundering herd
                        delay *= (1 + (asyncio.get_event_loop().time() % 0.1))
                    delay = min(delay, config.max_delay)  # Cap maximum delay

                    logger.warning(
                        "Retry attempt",
                        function=func.__name__,
                        attempt=attempt,
                        delay=delay,
                        error=str(e)
                    )

                    await asyncio.sleep(delay)

            # Should never reach here due to raise in loop
            raise last_exception or Exception("Retry failed")

        return wrapper
    return decorator 