from typing import Type, Tuple, Callable, Any
import asyncio
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential: bool = True
    jitter: bool = True

def with_retry(
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    config: RetryConfig = None
):
    """Decorator for retry logic with exponential backoff"""
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
                        logger.error(
                            "Max retry attempts reached",
                            function=func.__name__,
                            attempt=attempt,
                            error=str(e)
                        )
                        raise

                    # Calculate delay with exponential backoff and jitter
                    delay = config.base_delay
                    if config.exponential:
                        delay *= (2 ** (attempt - 1))
                    if config.jitter:
                        delay *= (1 + (asyncio.get_event_loop().time() % 0.1))
                    delay = min(delay, config.max_delay)

                    logger.warning(
                        "Retry attempt",
                        function=func.__name__,
                        attempt=attempt,
                        delay=delay,
                        error=str(e)
                    )

                    await asyncio.sleep(delay)

            # Should never reach here, but just in case
            raise last_exception or Exception("Retry failed")

        return wrapper
    return decorator 