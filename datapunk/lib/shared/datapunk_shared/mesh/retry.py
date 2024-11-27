from typing import TypeVar, Callable, Optional, Any
from dataclasses import dataclass
import asyncio
import random
import time
import structlog
from functools import wraps
from .metrics import RetryMetrics
from ..tracing import trace_method

logger = structlog.get_logger()
T = TypeVar('T')

"""
Resilient retry mechanism for Datapunk's service mesh layer.

This module implements an advanced retry policy system that supports:
- Exponential backoff with configurable jitter
- Detailed metrics collection
- Distributed tracing integration
- Service-specific retry configurations
- Enhanced error handling and recovery

Part of the service mesh reliability layer, working alongside the health check
and circuit breaker components to ensure robust service communication.
"""

@dataclass
class RetryConfig:
    """
    Configuration parameters for retry behavior.
    
    Designed to be customizable per service while maintaining reasonable defaults
    that prevent overwhelming downstream services during recovery.
    
    NOTE: max_delay should be set considering service SLAs and timeout configurations
    """
    max_attempts: int = 3  # Maximum number of retry attempts before giving up
    initial_delay: float = 0.1  # Base delay for first retry (seconds)
    max_delay: float = 10.0  # Maximum delay cap to prevent excessive waiting
    exponential_base: float = 2  # Growth rate for exponential backoff
    jitter: bool = True  # Enable random jitter to prevent thundering herd
    jitter_factor: float = 0.1  # Maximum jitter as percentage of delay

class RetryPolicy:
    """
    Implements retry logic with exponential backoff, metrics, and tracing.
    
    Integrated with the service mesh for distributed system reliability:
    - Tracks retry attempts and success rates per service
    - Provides detailed telemetry for monitoring and debugging
    - Supports circuit breaker integration through metrics
    
    TODO: Add circuit breaker integration
    FIXME: Consider adding retry budget implementation
    """
    
    def __init__(self, config: RetryConfig = RetryConfig()):
        self.config = config
        self.metrics = RetryMetrics()
        self.logger = logger.bind(component="retry_policy")

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate next retry delay using exponential backoff and optional jitter.
        
        The delay increases exponentially but is capped at max_delay to prevent
        excessive waiting. Jitter helps prevent thundering herd problem in
        distributed systems by randomizing retry timing.
        """
        delay = min(
            self.config.initial_delay * (self.config.exponential_base ** attempt),
            self.config.max_delay
        )
        
        if self.config.jitter:
            jitter_range = delay * self.config.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)

    @trace_method("execute_with_retry")
    async def execute_with_retry(
        self,
        operation: Callable[..., T],
        *args,
        retry_on: tuple = (Exception,),
        service_name: str = "unknown",
        operation_name: str = "unknown",
        **kwargs
    ) -> T:
        """
        Execute operation with configurable retry logic and telemetry.
        
        Implements the core retry mechanism with:
        - Progressive backoff between attempts
        - Detailed metric collection per service/operation
        - Distributed tracing integration
        - Comprehensive error logging
        
        NOTE: Consider service dependencies when configuring retry_on exceptions
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                start_time = time.time()
                
                # Add trace context
                self.tracing.set_attribute("retry.attempt", attempt + 1)
                self.tracing.set_attribute("retry.max_attempts", self.config.max_attempts)
                
                with self.tracing.start_span("operation_execution") as span:
                    result = await operation(*args, **kwargs)
                    span.set_attribute("duration", time.time() - start_time)
                
                # Record successful attempt
                self.metrics.record_success(
                    service_name,
                    operation_name,
                    attempt + 1,
                    time.time() - start_time
                )
                
                return result
                
            except retry_on as e:
                last_exception = e
                self.tracing.record_exception(e)
                
                self.metrics.record_failure(
                    service_name,
                    operation_name,
                    attempt + 1,
                    str(e)
                )
                
                if attempt + 1 < self.config.max_attempts:
                    delay = self.calculate_delay(attempt)
                    
                    self.tracing.add_event("retry_delay", {
                        "attempt": attempt + 1,
                        "delay": delay
                    })
                    
                    self.logger.warning("operation_failed_retrying",
                                      service=service_name,
                                      operation=operation_name,
                                      attempt=attempt + 1,
                                      delay=delay,
                                      error=str(e))
                    
                    await asyncio.sleep(delay)
                else:
                    self.logger.error("operation_failed_max_retries",
                                    service=service_name,
                                    operation=operation_name,
                                    attempts=self.config.max_attempts,
                                    error=str(e))
        
        raise last_exception

def with_retry(
    retry_config: Optional[RetryConfig] = None,
    retry_on: tuple = (Exception,),
    service_name: str = "unknown",
    operation_name: Optional[str] = None
):
    """Decorator for retry logic."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        policy = RetryPolicy(retry_config or RetryConfig())
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            op_name = operation_name or func.__name__
            return await policy.execute_with_retry(
                func,
                *args,
                retry_on=retry_on,
                service_name=service_name,
                operation_name=op_name,
                **kwargs
            )
        return wrapper
    return decorator 

class EnhancedRetryPolicy(RetryPolicy):
    """
    Extended retry policy with Redis-backed resilience features.
    
    Adds distributed state management and coordination:
    - Shared retry state across service instances
    - Cluster-wide retry budget management
    - Enhanced failure detection and recovery
    
    TODO: Implement retry budget sharing across instances
    """
    def __init__(self,
                 config: RetryConfig,
                 redis_client,
                 service_id: str):
        super().__init__(config)
        self.resilient_policy = ResilientRetryPolicy(
            redis_client,
            config,
            service_id
        )
    
    async def execute_with_retry(self,
                               operation: Callable[..., T],
                               *args,
                               operation_name: str = None,
                               **kwargs) -> T:
        """Execute with enhanced retry protection."""
        return await self.resilient_policy.execute_with_retry(
            operation,
            operation_name or operation.__name__,
            *args,
            **kwargs
        ) 