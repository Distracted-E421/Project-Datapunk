from typing import Dict, Any, Optional, Callable, Awaitable, Type, List
import time
import logging
import traceback
from dataclasses import dataclass
from .error_types import ServiceError, ErrorCategory, ErrorSeverity, ErrorContext
from ..monitoring.metrics import MetricsClient
from ..monitoring.tracing import TracingClient

@dataclass
class ErrorHandlerConfig:
    service_id: str
    max_retries: int = 3
    enable_metrics: bool = True
    enable_tracing: bool = True
    log_level: str = "INFO"
    default_http_status: int = 500

class ErrorHandler:
    def __init__(
        self,
        config: ErrorHandlerConfig,
        metrics_client: Optional[MetricsClient] = None,
        tracing_client: Optional[TracingClient] = None
    ):
        self.config = config
        self.logger = logging.getLogger(f"error_handler.{config.service_id}")
        self.metrics = metrics_client
        self.tracing = tracing_client
        
        # Error handlers by category
        self._handlers: Dict[ErrorCategory, List[Callable]] = {
            category: [] for category in ErrorCategory
        }
        
        # Recovery strategies
        self._recovery_strategies: Dict[str, Callable] = {}
        
        # Initialize default handlers
        self._init_default_handlers()

    def _init_default_handlers(self) -> None:
        """Initialize default error handlers for each category"""
        # Authentication errors
        self.add_handler(
            ErrorCategory.AUTHENTICATION,
            lambda err: self._handle_auth_error(err)
        )
        
        # Network errors
        self.add_handler(
            ErrorCategory.NETWORK,
            lambda err: self._handle_network_error(err)
        )
        
        # Resource errors
        self.add_handler(
            ErrorCategory.RESOURCE,
            lambda err: self._handle_resource_error(err)
        )

    async def handle_error(
        self,
        error: ServiceError,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Handle a service error"""
        try:
            start_time = time.time()
            
            # Record error metrics
            if self.metrics:
                await self.metrics.increment_counter(
                    'service_errors_total',
                    {
                        'service_id': self.config.service_id,
                        'category': error.category.value,
                        'severity': error.severity.value
                    }
                )

            # Record error trace
            if self.tracing:
                await self.tracing.record_error(error)

            # Log error
            self._log_error(error)

            # Execute category-specific handlers
            for handler in self._handlers.get(error.category, []):
                try:
                    result = await handler(error)
                    if result:
                        return result
                except Exception as e:
                    self.logger.error(f"Error handler failed: {str(e)}")

            # Try recovery if available and retries allowed
            if error.retry_allowed and retry_count < self.config.max_retries:
                recovery_strategy = self._recovery_strategies.get(error.category.value)
                if recovery_strategy:
                    try:
                        return await recovery_strategy(error, retry_count + 1)
                    except Exception as e:
                        self.logger.error(f"Recovery strategy failed: {str(e)}")

            # Return standardized error response
            return self._create_error_response(error)

        finally:
            if self.metrics:
                duration = time.time() - start_time
                await self.metrics.record_histogram(
                    'error_handling_duration_seconds',
                    duration,
                    {'category': error.category.value}
                )

    def add_handler(
        self,
        category: ErrorCategory,
        handler: Callable[[ServiceError], Awaitable[Optional[Dict[str, Any]]]]
    ) -> None:
        """Add a custom error handler for a category"""
        self._handlers[category].append(handler)

    def add_recovery_strategy(
        self,
        category: str,
        strategy: Callable[[ServiceError, int], Awaitable[Optional[Dict[str, Any]]]]
    ) -> None:
        """Add a recovery strategy for an error category"""
        self._recovery_strategies[category] = strategy

    def _log_error(self, error: ServiceError) -> None:
        """Log error with appropriate level and context"""
        log_level = logging.getLevelName(error.severity.value.upper())
        
        log_data = {
            'error_code': error.code,
            'category': error.category.value,
            'service_id': error.context.service_id,
            'operation': error.context.operation,
            'trace_id': error.context.trace_id,
            'timestamp': error.context.timestamp,
            'stack_trace': traceback.format_exc() if error.cause else None
        }

        self.logger.log(
            log_level,
            f"{error.message} - {error.code}",
            extra=log_data
        )

    def _create_error_response(self, error: ServiceError) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'error': {
                'code': error.code,
                'message': error.message,
                'category': error.category.value,
                'severity': error.severity.value,
                'trace_id': error.context.trace_id,
                'timestamp': error.context.timestamp,
                'retry_allowed': error.retry_allowed
            }
        }

    async def _handle_auth_error(self, error: ServiceError) -> Optional[Dict[str, Any]]:
        """Handle authentication errors"""
        # Implement authentication error specific handling
        pass

    async def _handle_network_error(self, error: ServiceError) -> Optional[Dict[str, Any]]:
        """Handle network errors"""
        # Implement network error specific handling
        pass

    async def _handle_resource_error(self, error: ServiceError) -> Optional[Dict[str, Any]]:
        """Handle resource errors"""
        # Implement resource error specific handling
        pass 