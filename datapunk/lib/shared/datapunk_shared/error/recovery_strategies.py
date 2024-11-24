from typing import Dict, Any, Optional, Callable, Awaitable
import asyncio
import time
import logging
from dataclasses import dataclass
from .error_types import ServiceError, ErrorCategory, ErrorSeverity, ErrorContext

@dataclass
class RetryConfig:
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2
    jitter: bool = True

class RecoveryStrategies:
    def __init__(self, retry_config: RetryConfig = RetryConfig()):
        self.retry_config = retry_config
        self.logger = logging.getLogger(__name__)

    async def network_recovery(
        self,
        error: ServiceError,
        retry_count: int,
        operation: Callable
    ) -> Optional[Dict[str, Any]]:
        """Recovery strategy for network errors with exponential backoff"""
        try:
            delay = self._calculate_backoff(retry_count)
            self.logger.info(f"Network recovery: waiting {delay}s before retry {retry_count}")
            await asyncio.sleep(delay)
            
            return await operation()

        except Exception as e:
            self.logger.error(f"Network recovery failed: {str(e)}")
            return None

    async def cache_recovery(
        self,
        error: ServiceError,
        retry_count: int,
        fallback_operation: Callable
    ) -> Optional[Dict[str, Any]]:
        """Recovery strategy for cache errors with fallback to source"""
        try:
            self.logger.info("Cache recovery: attempting fallback to source")
            return await fallback_operation()

        except Exception as e:
            self.logger.error(f"Cache recovery failed: {str(e)}")
            return None

    async def database_recovery(
        self,
        error: ServiceError,
        retry_count: int,
        operation: Callable,
        connection_manager: Any
    ) -> Optional[Dict[str, Any]]:
        """Recovery strategy for database errors with connection reset"""
        try:
            self.logger.info("Database recovery: attempting connection reset")
            await connection_manager.reset_connections()
            
            delay = self._calculate_backoff(retry_count)
            await asyncio.sleep(delay)
            
            return await operation()

        except Exception as e:
            self.logger.error(f"Database recovery failed: {str(e)}")
            return None

    async def resource_recovery(
        self,
        error: ServiceError,
        retry_count: int,
        operation: Callable,
        resource_manager: Any
    ) -> Optional[Dict[str, Any]]:
        """Recovery strategy for resource errors with cleanup"""
        try:
            self.logger.info("Resource recovery: attempting resource cleanup")
            await resource_manager.cleanup_resources()
            
            delay = self._calculate_backoff(retry_count)
            await asyncio.sleep(delay)
            
            return await operation()

        except Exception as e:
            self.logger.error(f"Resource recovery failed: {str(e)}")
            return None

    def _calculate_backoff(self, retry_count: int) -> float:
        """Calculate exponential backoff with jitter"""
        delay = min(
            self.retry_config.initial_delay * (
                self.retry_config.exponential_base ** (retry_count - 1)
            ),
            self.retry_config.max_delay
        )
        
        if self.retry_config.jitter:
            import random
            delay *= (0.5 + random.random())
        
        return delay 