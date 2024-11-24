from functools import wraps
from typing import Callable, Any, Optional, Type
import time
import uuid
from .error_types import ServiceError, ErrorContext, ErrorCategory, ErrorSeverity

def handle_errors(
    error_handler: 'ErrorHandler',
    operation: str,
    retryable: bool = True,
    error_category: Optional[ErrorCategory] = None,
    error_severity: Optional[ErrorSeverity] = None
):
    """Decorator for handling errors in service methods"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except ServiceError as e:
                # Pass through existing ServiceErrors
                return await error_handler.handle_error(e)
            except Exception as e:
                # Convert other exceptions to ServiceError
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