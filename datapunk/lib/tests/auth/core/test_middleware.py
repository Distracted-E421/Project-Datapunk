"""
Core Middleware Tests
----------------

Tests the core middleware system including:
- Request processing
- Response handling
- Authentication
- Authorization
- Rate limiting
- Logging
- Error handling

Run with: pytest -v test_middleware.py
"""

import pytest
from datetime import datetime
import json
from unittest.mock import AsyncMock, Mock, patch

from datapunk_shared.auth.core.middleware import (
    AuthMiddleware,
    RequestContext,
    ResponseContext,
    MiddlewareChain,
    MiddlewareConfig,
    SecurityMiddleware,
    LoggingMiddleware
)
from datapunk_shared.auth.core.exceptions import AuthError

# Test Fixtures

@pytest.fixture
def auth_client():
    """Mock auth client for testing."""
    client = AsyncMock()
    client.validate = AsyncMock()
    client.authenticate = AsyncMock()
    return client

@pytest.fixture
def logger_client():
    """Mock logger client for testing."""
    client = Mock()
    client.info = Mock()
    client.error = Mock()
    return client

@pytest.fixture
def middleware_config():
    """Create middleware configuration for testing."""
    return MiddlewareConfig(
        enabled=True,
        auth_required=True,
        rate_limit=100,
        timeout=30
    )

@pytest.fixture
def auth_middleware(auth_client, logger_client, middleware_config):
    """Create auth middleware for testing."""
    return AuthMiddleware(
        auth=auth_client,
        logger=logger_client,
        config=middleware_config
    )

@pytest.fixture
def request_context():
    """Create request context for testing."""
    return RequestContext(
        request_id="test_request",
        path="/api/test",
        method="GET",
        headers={
            "Authorization": "Bearer test_token",
            "X-Request-ID": "test_request"
        },
        body={"test": "data"}
    )

@pytest.fixture
def response_context():
    """Create response context for testing."""
    return ResponseContext(
        status_code=200,
        headers={},
        body={"result": "success"}
    )

# Request Processing Tests

@pytest.mark.asyncio
async def test_request_processing(auth_middleware, request_context):
    """Test request processing."""
    # Mock successful auth
    auth_middleware.auth.validate.return_value = True
    
    result = await auth_middleware.process_request(request_context)
    
    assert result.success is True
    assert result.context.user_id is not None
    assert result.context.authenticated is True
    
    # Verify auth called
    auth_middleware.auth.validate.assert_called_once()
    
    # Verify logging
    auth_middleware.logger.info.assert_called_once()

@pytest.mark.asyncio
async def test_request_validation(auth_middleware, request_context):
    """Test request validation."""
    # Missing auth header
    request_context.headers.pop("Authorization")
    
    with pytest.raises(AuthError) as exc:
        await auth_middleware.process_request(request_context)
    assert "missing authorization" in str(exc.value).lower()
    
    # Invalid token
    request_context.headers["Authorization"] = "Invalid"
    with pytest.raises(AuthError) as exc:
        await auth_middleware.process_request(request_context)
    assert "invalid token" in str(exc.value).lower()

# Response Handling Tests

@pytest.mark.asyncio
async def test_response_handling(auth_middleware, response_context):
    """Test response handling."""
    result = await auth_middleware.process_response(response_context)
    
    assert result.success is True
    assert "X-Request-ID" in result.context.headers
    
    # Verify logging
    auth_middleware.logger.info.assert_called_once()

@pytest.mark.asyncio
async def test_error_response(auth_middleware):
    """Test error response handling."""
    error_response = ResponseContext(
        status_code=500,
        body={"error": "Internal error"}
    )
    
    result = await auth_middleware.process_response(error_response)
    
    assert result.success is True
    assert result.context.status_code == 500
    
    # Verify error logging
    auth_middleware.logger.error.assert_called_once()

# Middleware Chain Tests

def test_middleware_chain():
    """Test middleware chain execution."""
    chain = MiddlewareChain([
        LoggingMiddleware(),
        SecurityMiddleware(),
        AuthMiddleware()
    ])
    
    assert len(chain.middleware) == 3
    assert isinstance(chain.middleware[0], LoggingMiddleware)
    assert isinstance(chain.middleware[1], SecurityMiddleware)
    assert isinstance(chain.middleware[2], AuthMiddleware)

@pytest.mark.asyncio
async def test_chain_execution(auth_middleware, request_context):
    """Test middleware chain execution."""
    chain = MiddlewareChain([
        LoggingMiddleware(),
        auth_middleware
    ])
    
    result = await chain.execute(request_context)
    
    assert result.success is True
    assert len(result.processed) == 2
    assert all(p.success for p in result.processed)

# Security Tests

@pytest.mark.asyncio
async def test_security_middleware():
    """Test security middleware."""
    security = SecurityMiddleware()
    
    request = RequestContext(
        headers={
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block"
        }
    )
    
    result = await security.process_request(request)
    
    assert result.success is True
    assert result.context.headers["X-Frame-Options"] == "DENY"
    assert result.context.headers["X-XSS-Protection"] == "1; mode=block"

@pytest.mark.asyncio
async def test_security_headers(auth_middleware, response_context):
    """Test security headers in response."""
    result = await auth_middleware.process_response(response_context)
    
    # Verify security headers
    headers = result.context.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in headers

# Logging Tests

@pytest.mark.asyncio
async def test_logging_middleware():
    """Test logging middleware."""
    logger = Mock()
    middleware = LoggingMiddleware(logger=logger)
    
    request = RequestContext(
        request_id="test_request",
        method="GET",
        path="/api/test"
    )
    
    await middleware.process_request(request)
    
    # Verify logging
    logger.info.assert_called_once()
    log_message = logger.info.call_args[0][0]
    assert "test_request" in log_message
    assert "GET" in log_message
    assert "/api/test" in log_message

@pytest.mark.asyncio
async def test_error_logging(auth_middleware, request_context):
    """Test error logging."""
    # Simulate error
    auth_middleware.auth.validate.side_effect = AuthError("Auth failed")
    
    with pytest.raises(AuthError):
        await auth_middleware.process_request(request_context)
    
    # Verify error logging
    auth_middleware.logger.error.assert_called_once()
    error_log = auth_middleware.logger.error.call_args[0][0]
    assert "Auth failed" in error_log
    assert request_context.request_id in str(error_log)

# Performance Tests

@pytest.mark.asyncio
async def test_middleware_performance(auth_middleware, request_context):
    """Test middleware performance."""
    # Process multiple requests
    start_time = datetime.utcnow()
    for _ in range(100):
        try:
            await auth_middleware.process_request(request_context)
        except AuthError:
            pass
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 1.0  # Should process 100 requests within 1 second

@pytest.mark.asyncio
async def test_chain_performance():
    """Test middleware chain performance."""
    chain = MiddlewareChain([
        LoggingMiddleware(),
        SecurityMiddleware(),
        AuthMiddleware()
    ])
    
    request = RequestContext(
        request_id="test_request",
        method="GET",
        path="/api/test"
    )
    
    # Process multiple requests through chain
    start_time = datetime.utcnow()
    for _ in range(100):
        await chain.execute(request)
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 2.0  # Should process 100 requests through chain within 2 seconds 