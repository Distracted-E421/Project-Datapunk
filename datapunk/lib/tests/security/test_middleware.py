import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from datapunk_shared.security.middleware import (
    SecurityMiddleware,
    MiddlewareConfig,
    SecurityContext,
    SecurityError
)

@pytest.fixture
def middleware_config():
    return MiddlewareConfig(
        name="test_middleware",
        enabled_checks=[
            "authentication",
            "authorization",
            "rate_limit",
            "input_validation"
        ],
        authentication={
            "token_header": "X-Auth-Token",
            "token_type": "JWT",
            "public_key_path": "/path/to/public.key"
        },
        authorization={
            "roles_header": "X-User-Roles",
            "required_roles": ["user", "admin"]
        },
        rate_limit={
            "requests_per_minute": 60,
            "burst_size": 10
        },
        input_validation={
            "max_body_size": 1024 * 1024,  # 1MB
            "allowed_content_types": ["application/json"]
        }
    )

@pytest.fixture
def mock_request():
    return MagicMock(
        headers={
            "X-Auth-Token": "valid.jwt.token",
            "X-User-Roles": "user,admin",
            "Content-Type": "application/json"
        },
        body=b'{"key": "value"}',
        method="POST",
        path="/api/test"
    )

@pytest.fixture
async def security_middleware(middleware_config):
    middleware = SecurityMiddleware(middleware_config)
    await middleware.initialize()
    return middleware

@pytest.mark.asyncio
async def test_middleware_initialization(security_middleware, middleware_config):
    """Test security middleware initialization"""
    assert security_middleware.config == middleware_config
    assert security_middleware.is_initialized
    assert len(security_middleware.enabled_checks) == len(middleware_config.enabled_checks)

@pytest.mark.asyncio
async def test_authentication_check(security_middleware, mock_request):
    """Test authentication check"""
    with patch('jwt.decode') as mock_decode:
        mock_decode.return_value = {
            "sub": "test_user",
            "exp": datetime.now().timestamp() + 3600
        }
        
        result = await security_middleware.check_authentication(mock_request)
        assert result.is_authenticated
        assert result.user_id == "test_user"

@pytest.mark.asyncio
async def test_authorization_check(security_middleware, mock_request):
    """Test authorization check"""
    context = SecurityContext(
        user_id="test_user",
        roles=["user", "admin"]
    )
    
    result = await security_middleware.check_authorization(mock_request, context)
    assert result.is_authorized
    assert not result.missing_roles

@pytest.mark.asyncio
async def test_rate_limit_check(security_middleware, mock_request):
    """Test rate limit check"""
    # First request should pass
    result = await security_middleware.check_rate_limit(mock_request)
    assert result.is_allowed
    
    # Simulate rate limit exceeded
    for _ in range(security_middleware.config.rate_limit["requests_per_minute"]):
        await security_middleware.check_rate_limit(mock_request)
    
    result = await security_middleware.check_rate_limit(mock_request)
    assert not result.is_allowed
    assert "rate limit exceeded" in str(result.error)

@pytest.mark.asyncio
async def test_input_validation(security_middleware, mock_request):
    """Test input validation"""
    # Valid request
    result = await security_middleware.validate_input(mock_request)
    assert result.is_valid
    
    # Invalid content type
    invalid_request = MagicMock(
        headers={"Content-Type": "text/plain"},
        body=b'plain text'
    )
    result = await security_middleware.validate_input(invalid_request)
    assert not result.is_valid
    assert "content type" in str(result.error)
    
    # Body too large
    large_request = MagicMock(
        headers={"Content-Type": "application/json"},
        body=b'{"key": "' + b'x' * (1024 * 1024 + 1) + b'"}'
    )
    result = await security_middleware.validate_input(large_request)
    assert not result.is_valid
    assert "body size" in str(result.error)

@pytest.mark.asyncio
async def test_complete_middleware_chain(security_middleware, mock_request):
    """Test complete middleware chain"""
    with patch('jwt.decode') as mock_decode:
        mock_decode.return_value = {
            "sub": "test_user",
            "exp": datetime.now().timestamp() + 3600
        }
        
        result = await security_middleware.process(mock_request)
        assert result.success
        assert result.context.user_id == "test_user"
        assert set(result.context.roles) == {"user", "admin"}

@pytest.mark.asyncio
async def test_error_handling(security_middleware):
    """Test error handling"""
    # Test with invalid request
    with pytest.raises(SecurityError):
        await security_middleware.process(None)
    
    # Test with missing required headers
    invalid_request = MagicMock(headers={})
    result = await security_middleware.process(invalid_request)
    assert not result.success
    assert "missing" in str(result.error)

@pytest.mark.asyncio
async def test_middleware_hooks(security_middleware, mock_request):
    """Test middleware hooks"""
    pre_process = AsyncMock()
    post_process = AsyncMock()
    
    security_middleware.add_pre_process_hook(pre_process)
    security_middleware.add_post_process_hook(post_process)
    
    await security_middleware.process(mock_request)
    
    pre_process.assert_called_once()
    post_process.assert_called_once()

@pytest.mark.asyncio
async def test_middleware_metrics(security_middleware, mock_request):
    """Test middleware metrics collection"""
    metrics = []
    security_middleware.set_metrics_callback(metrics.append)
    
    await security_middleware.process(mock_request)
    
    assert len(metrics) > 0
    assert any(m["type"] == "request_processed" for m in metrics)
    assert any(m["type"] == "security_check_duration" for m in metrics)

@pytest.mark.asyncio
async def test_custom_security_checks(security_middleware, mock_request):
    """Test custom security checks"""
    # Add custom check
    async def custom_check(request, context):
        return request.headers.get("X-Custom-Header") == "valid"
    
    security_middleware.add_security_check("custom", custom_check)
    
    # Test with valid custom header
    valid_request = MagicMock(
        headers={
            **mock_request.headers,
            "X-Custom-Header": "valid"
        }
    )
    result = await security_middleware.process(valid_request)
    assert result.success
    
    # Test with invalid custom header
    invalid_request = MagicMock(
        headers={
            **mock_request.headers,
            "X-Custom-Header": "invalid"
        }
    )
    result = await security_middleware.process(invalid_request)
    assert not result.success

@pytest.mark.asyncio
async def test_context_propagation(security_middleware, mock_request):
    """Test security context propagation"""
    with patch('jwt.decode') as mock_decode:
        mock_decode.return_value = {
            "sub": "test_user",
            "exp": datetime.now().timestamp() + 3600,
            "custom_claim": "test_value"
        }
        
        result = await security_middleware.process(mock_request)
        assert result.context.get_claim("custom_claim") == "test_value" 