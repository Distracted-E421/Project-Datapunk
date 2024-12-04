import pytest
import asyncio
from functools import wraps
from unittest.mock import Mock, patch
from datapunk_shared.error.decorators import (
    retry,
    circuit_breaker,
    error_handler,
    log_errors,
    fallback,
    timeout
)
from datapunk_shared.error.error_types import (
    ErrorSeverity,
    ErrorCategory,
    DatapunkError
)

@pytest.fixture
def mock_logger():
    return Mock()

def test_retry_decorator():
    attempt_count = 0
    
    @retry(max_attempts=3, delay_seconds=0.1)
    def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise DatapunkError("Temporary error")
        return "success"
    
    result = flaky_function()
    assert result == "success"
    assert attempt_count == 3

@pytest.mark.asyncio
async def test_async_retry_decorator():
    attempt_count = 0
    
    @retry(max_attempts=3, delay_seconds=0.1)
    async def async_flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise DatapunkError("Temporary error")
        return "success"
    
    result = await async_flaky_function()
    assert result == "success"
    assert attempt_count == 3

def test_circuit_breaker_decorator():
    call_count = 0
    
    @circuit_breaker(failure_threshold=2, reset_timeout=0.1)
    def protected_function():
        nonlocal call_count
        call_count += 1
        raise DatapunkError("Service error")
    
    # First two calls should raise the original error
    for _ in range(2):
        with pytest.raises(DatapunkError):
            protected_function()
    
    # Third call should raise CircuitBreakerError
    with pytest.raises(DatapunkError) as exc_info:
        protected_function()
    assert "Circuit breaker open" in str(exc_info.value)

def test_error_handler_decorator(mock_logger):
    handled_errors = []
    
    def custom_handler(error):
        handled_errors.append(error)
        return "handled"
    
    @error_handler(handler=custom_handler)
    def function_with_error():
        raise DatapunkError("Test error")
    
    result = function_with_error()
    assert result == "handled"
    assert len(handled_errors) == 1
    assert isinstance(handled_errors[0], DatapunkError)

def test_log_errors_decorator(mock_logger):
    with patch('logging.getLogger') as mock_get_logger:
        mock_get_logger.return_value = mock_logger
        
        @log_errors(logger=mock_logger)
        def function_with_error():
            raise DatapunkError("Test error")
        
        with pytest.raises(DatapunkError):
            function_with_error()
        
        mock_logger.error.assert_called_once()

def test_fallback_decorator():
    @fallback(default_value="fallback")
    def failing_function():
        raise DatapunkError("Primary error")
    
    result = failing_function()
    assert result == "fallback"
    
    @fallback(default_value="fallback")
    def successful_function():
        return "success"
    
    result = successful_function()
    assert result == "success"

@pytest.mark.asyncio
async def test_timeout_decorator():
    @timeout(seconds=0.1)
    async def slow_function():
        await asyncio.sleep(0.2)
        return "done"
    
    with pytest.raises(DatapunkError) as exc_info:
        await slow_function()
    assert "Operation timed out" in str(exc_info.value)
    
    @timeout(seconds=0.2)
    async def fast_function():
        await asyncio.sleep(0.1)
        return "done"
    
    result = await fast_function()
    assert result == "done"

def test_decorator_composition():
    @retry(max_attempts=2)
    @circuit_breaker(failure_threshold=3)
    @fallback(default_value="fallback")
    def complex_function():
        raise DatapunkError("Service error")
    
    result = complex_function()
    assert result == "fallback"

@pytest.mark.asyncio
async def test_async_decorator_composition():
    @retry(max_attempts=2)
    @circuit_breaker(failure_threshold=3)
    @fallback(default_value="fallback")
    async def async_complex_function():
        raise DatapunkError("Service error")
    
    result = await async_complex_function()
    assert result == "fallback"

def test_error_handler_inheritance():
    class BaseError(Exception):
        pass
    
    class SpecificError(BaseError):
        pass
    
    handled_errors = []
    
    def base_handler(error):
        handled_errors.append(("base", error))
        return None
    
    def specific_handler(error):
        handled_errors.append(("specific", error))
        return "handled"
    
    @error_handler(handler=specific_handler, error_type=SpecificError)
    @error_handler(handler=base_handler, error_type=BaseError)
    def function_with_specific_error():
        raise SpecificError("Test error")
    
    result = function_with_specific_error()
    assert result == "handled"
    assert len(handled_errors) == 1
    assert handled_errors[0][0] == "specific" 