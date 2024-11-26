from functools import wraps
from typing import Callable, Any, Optional, Type
import time
import uuid
from .error_types import ServiceError, ErrorContext, ErrorCategory, ErrorSeverity

"""
Error Handling Decorators for Datapunk Services

This module provides decorators for standardized error handling across Datapunk services.
It implements the service mesh error handling requirements and ensures consistent
error reporting and recovery behavior throughout the system.

Key Features:
- Standardized error conversion
- Automatic context enrichment
- Metrics integration
- Retry policy enforcement
- Error categorization

Integration Points:
- ErrorHandler for centralized error processing
- Service mesh error reporting
- Metrics collection
- Distributed tracing

NOTE: All service methods should use these decorators to ensure consistent
error handling and monitoring across the system.
"""

def handle_errors(
    error_handler: 'ErrorHandler',
    operation: str,
    retryable: bool = True,
    error_category: Optional[ErrorCategory] = None,
    error_severity: Optional[ErrorSeverity] = None
):
    """
    Decorator for standardized error handling in service methods.
    
    Implements Datapunk's error handling requirements:
    - Automatic error context enrichment
    - Error categorization and severity assignment
    - Retry policy enforcement
    - Metrics collection
    
    Usage:
    ```python
    @handle_errors(error_handler, "user_operation")
    async def user_method():
        # Method implementation
    ```
    
    IMPORTANT: The operation name is used for error codes and metrics.
    Use consistent naming across related operations for better observability.
    
    NOTE: Set retryable=False for operations that should not be retried
    (e.g., non-idempotent operations or those with side effects)
    
    TODO: Add support for custom error transformers
    TODO: Implement circuit breaker integration
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                # Execute the wrapped function
                return await func(*args, **kwargs)
            except ServiceError as e:
                # Pass through existing ServiceErrors to maintain context
                # IMPORTANT: This preserves the original error context
                return await error_handler.handle_error(e)
            except Exception as e:
                # Convert other exceptions to ServiceError with enriched context
                # This ensures consistent error handling across all services
                
                # Create error context with operation metadata
                # NOTE: UUID is used for correlation across distributed traces
                context = ErrorContext(
                    service_id=error_handler.config.service_id,
                    operation=operation,
                    trace_id=str(uuid.uuid4()),
                    timestamp=time.time(),
                    additional_data={
                        'args': str(args),
                        'kwargs': str(kwargs)
                    }
                )
                
                # Create standardized ServiceError
                # This enables consistent error handling and reporting
                error = ServiceError(
                    code=f"ERR_{operation.upper()}",
                    message=str(e),
                    category=error_category or ErrorCategory.BUSINESS_LOGIC,
                    severity=error_severity or ErrorSeverity.ERROR,
                    context=context,
                    retry_allowed=retryable,
                    cause=e
                )
                
                return await error_handler.handle_error(error)
        
        return wrapper
    
    return decorator 