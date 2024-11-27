from typing import Dict, Any, Optional, Callable
import logging
import time
from .error_types import ServiceError, ErrorCategory, ErrorSeverity
from .recovery_strategies import RecoveryStrategies

class ErrorHandlers:
    """
    Collection of specialized error handlers for different error categories.
    
    Each handler implements category-specific logic for:
    - Error recovery attempts
    - Resource cleanup
    - Client response generation
    - Monitoring integration
    
    IMPORTANT: Handlers should be stateless to ensure thread safety
    and prevent resource leaks.
    
    TODO: Add metrics collection for handler success/failure rates
    TODO: Implement handler-specific circuit breakers
    """

    def __init__(
        self,
        recovery_strategies: RecoveryStrategies,
        circuit_breaker: Optional[Any] = None
    ):
        self.recovery = recovery_strategies
        self.circuit_breaker = circuit_breaker
        self.logger = logging.getLogger(__name__)

    async def handle_authentication_error(
        self,
        error: ServiceError,
        auth_service: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Handle authentication failures with token refresh attempts.
        
        Recovery Strategy:
        1. Check for expired token condition
        2. Attempt token refresh if possible
        3. Return new token or authentication required response
        
        NOTE: Token refresh should only be attempted if a valid
        refresh token is available in the context.
        """
        try:
            if error.context.additional_data.get('token_expired'):
                # Attempt token refresh
                new_token = await auth_service.refresh_token(
                    error.context.additional_data.get('refresh_token')
                )
                if new_token:
                    return {
                        'status': 'retry',
                        'new_token': new_token
                    }
            
            return {
                'status': 'error',
                'message': 'Authentication failed',
                'action_required': 'reauth'
            }

        except Exception as e:
            self.logger.error(f"Auth error handler failed: {str(e)}")
            return None

    async def handle_database_error(
        self,
        error: ServiceError,
        db_manager: Any,
        operation: Callable
    ) -> Optional[Dict[str, Any]]:
        """
        Handle database errors with connection and deadlock recovery.
        
        Recovery Strategy:
        1. Attempt connection recovery for connectivity issues
        2. Apply backoff delay for deadlocks
        3. Retry original operation if recovery succeeds
        
        IMPORTANT: Deadlock recovery includes random delay to
        prevent thundering herd problem during retries.
        """
        try:
            if "connection" in error.message.lower():
                return await self.recovery.database_recovery(
                    error,
                    1,
                    operation,
                    db_manager
                )
            
            if "deadlock" in error.message.lower():
                # Add random delay to help resolve deadlock
                await self.recovery._calculate_backoff(1)
                return await operation()
            
            return None

        except Exception as e:
            self.logger.error(f"Database error handler failed: {str(e)}")
            return None

    async def handle_rate_limit_error(
        self,
        error: ServiceError
    ) -> Optional[Dict[str, Any]]:
        """
        Handle rate limit violations with retry guidance.
        
        Response includes:
        - Retry delay duration
        - Human-readable message
        - Rate limit status
        
        NOTE: Retry delay is extracted from error context or
        defaults to 60 seconds if not specified.
        """
        try:
            retry_after = error.context.additional_data.get('retry_after', 60)
            return {
                'status': 'rate_limited',
                'retry_after': retry_after,
                'message': f'Rate limit exceeded. Try again in {retry_after} seconds'
            }

        except Exception as e:
            self.logger.error(f"Rate limit error handler failed: {str(e)}")
            return None

    async def handle_resource_error(
        self,
        error: ServiceError,
        resource_manager: Any,
        operation: Callable
    ) -> Optional[Dict[str, Any]]:
        """
        Handle resource exhaustion with optimization attempts.
        
        Recovery Strategy:
        1. Attempt resource optimization
        2. Retry operation if resources freed
        3. Return failure if optimization unsuccessful
        
        TODO: Add resource usage metrics collection
        TODO: Implement predictive resource optimization
        """
        try:
            if "insufficient" in error.message.lower():
                # Attempt to free up resources
                await resource_manager.optimize_resources()
                return await self.recovery.resource_recovery(
                    error,
                    1,
                    operation,
                    resource_manager
                )
            
            return None

        except Exception as e:
            self.logger.error(f"Resource error handler failed: {str(e)}")
            return None

    async def handle_network_error(
        self,
        error: ServiceError,
        operation: Callable
    ) -> Optional[Dict[str, Any]]:
        """
        Handle network failures with circuit breaker integration.
        
        Recovery Strategy:
        1. Check circuit breaker status
        2. Apply network recovery strategy if allowed
        3. Return service unavailable if circuit open
        
        IMPORTANT: Circuit breaker prevents cascading failures
        during network instability.
        """
        try:
            if self.circuit_breaker and not self.circuit_breaker.is_allowed():
                return {
                    'status': 'circuit_open',
                    'message': 'Service temporarily unavailable'
                }
            
            return await self.recovery.network_recovery(
                error,
                1,
                operation
            )

        except Exception as e:
            self.logger.error(f"Network error handler failed: {str(e)}")
            return None

    async def handle_validation_error(
        self,
        error: ServiceError
    ) -> Optional[Dict[str, Any]]:
        """Handle validation errors"""
        try:
            return {
                'status': 'validation_error',
                'errors': error.context.additional_data.get('validation_errors', []),
                'message': 'Validation failed'
            }

        except Exception as e:
            self.logger.error(f"Validation error handler failed: {str(e)}")
            return None

    async def handle_timeout_error(
        self,
        error: ServiceError,
        operation: Callable
    ) -> Optional[Dict[str, Any]]:
        """
        Handle timeout errors with progressive timeout increase.
        
        Recovery Strategy:
        1. Increase timeout by 50% for retry
        2. Update context with new timeout
        3. Retry operation with extended timeout
        
        NOTE: Timeout increase prevents premature failures for
        operations that occasionally require more time.
        """
        try:
            if error.retry_allowed:
                # Increase timeout for retry
                timeout = error.context.additional_data.get('timeout', 30)
                new_timeout = timeout * 1.5
                
                # Update context with new timeout
                error.context.additional_data['timeout'] = new_timeout
                
                return await operation()
            
            return None

        except Exception as e:
            self.logger.error(f"Timeout error handler failed: {str(e)}")
            return None 