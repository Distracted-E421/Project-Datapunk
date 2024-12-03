import pytest
from unittest.mock import Mock, patch
from datapunk_shared.error.handlers import (
    ErrorHandler,
    ErrorMiddleware,
    RecoveryStrategy,
    RetryStrategy
)
from datapunk_shared.error.error_types import (
    ErrorSeverity,
    ErrorCategory,
    DatapunkError
)

@pytest.fixture
def error_handler():
    return ErrorHandler()

@pytest.fixture
def error_middleware():
    return ErrorMiddleware()

@pytest.fixture
def mock_logger():
    return Mock()

def test_error_handler_registration(error_handler):
    # Test registering error handlers for different categories
    def handler_func(error):
        return "handled"
    
    error_handler.register(ErrorCategory.VALIDATION, handler_func)
    assert ErrorCategory.VALIDATION in error_handler.handlers
    
    # Test handler execution
    result = error_handler.handle(
        DatapunkError("test", category=ErrorCategory.VALIDATION)
    )
    assert result == "handled"

def test_error_handler_priority(error_handler):
    # Test handler priority system
    def handler1(error): return "handler1"
    def handler2(error): return "handler2"
    
    error_handler.register(ErrorCategory.SYSTEM, handler1, priority=1)
    error_handler.register(ErrorCategory.SYSTEM, handler2, priority=2)
    
    result = error_handler.handle(
        DatapunkError("test", category=ErrorCategory.SYSTEM)
    )
    assert result == "handler2"  # Higher priority handler should execute

def test_error_middleware_chain(error_middleware):
    # Test middleware chain execution
    async def middleware1(error, next_handler):
        error.context["m1"] = True
        return await next_handler(error)
    
    async def middleware2(error, next_handler):
        error.context["m2"] = True
        return await next_handler(error)
    
    error_middleware.use(middleware1)
    error_middleware.use(middleware2)
    
    error = DatapunkError("test", context={})
    error_middleware.process(error)
    
    assert error.context["m1"]
    assert error.context["m2"]

@pytest.mark.asyncio
async def test_retry_strategy():
    retry = RetryStrategy(max_attempts=3, delay_seconds=0.1)
    
    # Test successful retry
    attempt_count = 0
    async def operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise DatapunkError("Temporary error")
        return "success"
    
    result = await retry.execute(operation)
    assert result == "success"
    assert attempt_count == 3

@pytest.mark.asyncio
async def test_retry_strategy_max_attempts():
    retry = RetryStrategy(max_attempts=3, delay_seconds=0.1)
    
    # Test max attempts exceeded
    async def failing_operation():
        raise DatapunkError("Persistent error")
    
    with pytest.raises(DatapunkError):
        await retry.execute(failing_operation)

def test_error_handler_logging(error_handler, mock_logger):
    with patch('logging.getLogger') as mock_get_logger:
        mock_get_logger.return_value = mock_logger
        
        error = DatapunkError(
            "Test error",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SYSTEM
        )
        
        error_handler.handle(error)
        mock_logger.error.assert_called_once()

def test_recovery_strategy_selection():
    # Test strategy selection based on error type
    strategies = {
        ErrorCategory.NETWORK: RetryStrategy(max_attempts=3),
        ErrorCategory.SYSTEM: Mock(spec=RecoveryStrategy)
    }
    
    error = DatapunkError("test", category=ErrorCategory.NETWORK)
    strategy = strategies.get(error.category)
    assert isinstance(strategy, RetryStrategy)

@pytest.mark.asyncio
async def test_error_middleware_error_propagation(error_middleware):
    # Test error propagation through middleware chain
    async def failing_middleware(error, next_handler):
        raise ValueError("Middleware error")
    
    error_middleware.use(failing_middleware)
    
    with pytest.raises(ValueError):
        await error_middleware.process(
            DatapunkError("test")
        )

def test_error_handler_chain_of_responsibility(error_handler):
    # Test chain of responsibility pattern
    results = []
    
    def handler1(error):
        results.append(1)
        return None  # Continue chain
    
    def handler2(error):
        results.append(2)
        return "handled"  # Stop chain
    
    def handler3(error):
        results.append(3)
        return None
    
    error_handler.register(ErrorCategory.VALIDATION, handler1)
    error_handler.register(ErrorCategory.VALIDATION, handler2)
    error_handler.register(ErrorCategory.VALIDATION, handler3)
    
    error_handler.handle(
        DatapunkError("test", category=ErrorCategory.VALIDATION)
    )
    
    assert results == [1, 2]  # Handler 3 should not execute 