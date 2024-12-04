"""
Core Routes Tests
------------

Tests the core routing system including:
- Route registration
- Route matching
- Parameter handling
- Middleware integration
- Error handling
- Security controls
- Performance monitoring

Run with: pytest -v test_routes.py
"""

import pytest
from datetime import datetime
import json
from unittest.mock import AsyncMock, Mock, patch

from datapunk_shared.auth.core.routes import (
    Router,
    Route,
    RouteHandler,
    RouteConfig,
    RouteContext,
    RouteParams,
    RouteMiddleware
)
from datapunk_shared.auth.core.exceptions import RouteError

# Test Fixtures

@pytest.fixture
def middleware_client():
    """Mock middleware client for testing."""
    client = AsyncMock()
    client.process = AsyncMock()
    return client

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.timing = AsyncMock()
    return client

@pytest.fixture
def route_config():
    """Create route configuration for testing."""
    return RouteConfig(
        prefix="/api",
        version="v1",
        middleware_enabled=True
    )

@pytest.fixture
def router(middleware_client, metrics_client, route_config):
    """Create router for testing."""
    return Router(
        middleware=middleware_client,
        metrics=metrics_client,
        config=route_config
    )

@pytest.fixture
def route_context():
    """Create route context for testing."""
    return RouteContext(
        request_id="test_request",
        path="/api/v1/users",
        method="GET",
        params={"id": "123"},
        headers={
            "Authorization": "Bearer test_token",
            "Content-Type": "application/json"
        }
    )

# Route Registration Tests

def test_route_registration(router):
    """Test route registration."""
    # Register route
    @router.route("/users", methods=["GET"])
    async def get_users():
        return {"users": []}
    
    assert "/users" in router.routes
    assert "GET" in router.routes["/users"].methods
    assert router.routes["/users"].handler is not None

def test_route_validation(router):
    """Test route validation."""
    # Invalid path
    with pytest.raises(ValueError):
        @router.route("", methods=["GET"])
        async def invalid_route():
            pass
    
    # Invalid method
    with pytest.raises(ValueError):
        @router.route("/test", methods=["INVALID"])
        async def invalid_method():
            pass

def test_duplicate_routes(router):
    """Test duplicate route handling."""
    @router.route("/test", methods=["GET"])
    async def first_handler():
        pass
    
    # Duplicate route should raise error
    with pytest.raises(RouteError):
        @router.route("/test", methods=["GET"])
        async def second_handler():
            pass

# Route Matching Tests

@pytest.mark.asyncio
async def test_route_matching(router, route_context):
    """Test route matching."""
    # Register test route
    @router.route("/users", methods=["GET"])
    async def get_users():
        return {"users": []}
    
    match = router.match_route(route_context)
    assert match.found is True
    assert match.route.path == "/users"
    assert "GET" in match.route.methods

@pytest.mark.asyncio
async def test_parameter_matching(router):
    """Test parameter matching in routes."""
    # Register parameterized route
    @router.route("/users/{user_id}", methods=["GET"])
    async def get_user(user_id: str):
        return {"user_id": user_id}
    
    context = RouteContext(path="/api/v1/users/123")
    match = router.match_route(context)
    
    assert match.found is True
    assert match.params["user_id"] == "123"

# Parameter Handling Tests

def test_parameter_extraction():
    """Test parameter extraction from path."""
    route = Route("/users/{user_id}/posts/{post_id}")
    
    params = route.extract_params("/users/123/posts/456")
    assert params["user_id"] == "123"
    assert params["post_id"] == "456"

def test_parameter_validation():
    """Test parameter validation."""
    route = Route(
        "/users/{user_id}",
        params={
            "user_id": {
                "type": "string",
                "pattern": r"^\d+$"
            }
        }
    )
    
    # Valid parameter
    assert route.validate_params({"user_id": "123"}) is True
    
    # Invalid parameter
    assert route.validate_params({"user_id": "abc"}) is False

# Handler Tests

@pytest.mark.asyncio
async def test_handler_execution(router, route_context):
    """Test route handler execution."""
    # Register test handler
    @router.route("/test", methods=["GET"])
    async def test_handler(context: RouteContext):
        return {"success": True, "data": context.params}
    
    result = await router.execute_handler(test_handler, route_context)
    assert result["success"] is True
    assert "data" in result

@pytest.mark.asyncio
async def test_handler_error_handling(router, route_context):
    """Test handler error handling."""
    # Register handler that raises error
    @router.route("/error", methods=["GET"])
    async def error_handler():
        raise ValueError("Test error")
    
    with pytest.raises(RouteError) as exc:
        await router.execute_handler(error_handler, route_context)
    assert "Test error" in str(exc.value)

# Middleware Integration Tests

@pytest.mark.asyncio
async def test_middleware_integration(router, route_context):
    """Test middleware integration."""
    # Register middleware
    @router.middleware
    async def test_middleware(context: RouteContext, next_handler):
        context.metadata["middleware_executed"] = True
        return await next_handler(context)
    
    # Register route
    @router.route("/test", methods=["GET"])
    async def test_handler(context: RouteContext):
        return {"middleware_executed": context.metadata.get("middleware_executed")}
    
    result = await router.handle_request(route_context)
    assert result["middleware_executed"] is True

@pytest.mark.asyncio
async def test_middleware_chain(router, route_context):
    """Test middleware chain execution."""
    order = []
    
    @router.middleware
    async def first_middleware(context, next):
        order.append(1)
        return await next(context)
    
    @router.middleware
    async def second_middleware(context, next):
        order.append(2)
        return await next(context)
    
    @router.route("/test", methods=["GET"])
    async def test_handler():
        order.append(3)
        return {}
    
    await router.handle_request(route_context)
    assert order == [1, 2, 3]

# Security Tests

@pytest.mark.asyncio
async def test_security_middleware(router, route_context):
    """Test security middleware."""
    # Register security middleware
    @router.middleware
    async def security_middleware(context, next):
        if "Authorization" not in context.headers:
            raise SecurityError("Missing authorization")
        return await next(context)
    
    # Test with missing auth
    route_context.headers.pop("Authorization")
    with pytest.raises(SecurityError):
        await router.handle_request(route_context)

@pytest.mark.asyncio
async def test_route_protection(router):
    """Test route protection."""
    # Register protected route
    @router.route("/protected", methods=["GET"], require_auth=True)
    async def protected_handler():
        return {"protected": True}
    
    context = RouteContext(
        path="/api/v1/protected",
        headers={}  # No auth token
    )
    
    with pytest.raises(SecurityError):
        await router.handle_request(context)

# Performance Tests

@pytest.mark.asyncio
async def test_routing_performance(router):
    """Test routing performance."""
    # Register test routes
    for i in range(100):
        @router.route(f"/test{i}", methods=["GET"])
        async def handler():
            return {}
    
    # Test matching performance
    start_time = datetime.utcnow()
    for i in range(1000):
        context = RouteContext(path=f"/api/v1/test{i % 100}")
        router.match_route(context)
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 1.0  # Should match 1000 routes within 1 second

@pytest.mark.asyncio
async def test_concurrent_routing(router):
    """Test concurrent route handling."""
    # Register test route
    @router.route("/test", methods=["GET"])
    async def test_handler():
        return {"success": True}
    
    # Create multiple requests
    contexts = [
        RouteContext(path="/api/v1/test")
        for _ in range(100)
    ]
    
    # Process concurrently
    tasks = [router.handle_request(ctx) for ctx in contexts]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 100
    assert all(r["success"] for r in results)

# Metrics Collection Tests

@pytest.mark.asyncio
async def test_route_metrics(router, route_context):
    """Test route metrics collection."""
    @router.route("/test", methods=["GET"])
    async def test_handler():
        return {}
    
    await router.handle_request(route_context)
    
    # Verify metrics
    router.metrics.increment.assert_has_calls([
        mock.call("route_requests", tags={"path": "/test", "method": "GET"}),
        mock.call("route_success", tags={"path": "/test"})
    ])
    
    # Verify timing metrics
    router.metrics.timing.assert_called_with(
        "route_processing_time",
        mock.ANY,
        tags={"path": "/test"}
    )

@pytest.mark.asyncio
async def test_error_metrics(router, route_context):
    """Test error metrics collection."""
    @router.route("/error", methods=["GET"])
    async def error_handler():
        raise ValueError("Test error")
    
    try:
        await router.handle_request(route_context)
    except RouteError:
        pass
    
    # Verify error metrics
    router.metrics.increment.assert_called_with(
        "route_errors",
        tags={"path": "/error", "error_type": "ValueError"}
    ) 