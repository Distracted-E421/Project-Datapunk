import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import aiohttp
from aiohttp import web
from datapunk_shared.mesh.communication.rest import (
    RestServer,
    ServerConfig,
    RouteConfig,
    RestError,
    Middleware
)

@pytest.fixture
def server_config():
    return ServerConfig(
        host="localhost",
        port=8080,
        cors_enabled=True,
        compression_enabled=True,
        client_max_size=1024*1024  # 1MB
    )

@pytest.fixture
def rest_server(server_config):
    return RestServer(config=server_config)

@pytest.fixture
def sample_routes():
    return [
        RouteConfig(
            path="/api/test",
            method="GET",
            handler="test_handler",
            middleware=["auth", "logging"]
        ),
        RouteConfig(
            path="/api/data/{id}",
            method="POST",
            handler="data_handler",
            middleware=["auth", "validation"]
        )
    ]

@pytest.mark.asyncio
async def test_server_initialization(rest_server, server_config):
    assert rest_server.config == server_config
    assert not rest_server.is_running
    assert len(rest_server.routes) == 0

@pytest.mark.asyncio
async def test_route_registration(rest_server, sample_routes):
    # Mock handler
    async def test_handler(request):
        return web.json_response({"message": "Success"})
    
    for route in sample_routes:
        await rest_server.register_route(
            path=route.path,
            method=route.method,
            handler=test_handler,
            middleware=route.middleware
        )
    
    assert len(rest_server.routes) == len(sample_routes)
    assert all(r.path in [route.path for route in sample_routes] 
              for r in rest_server.routes)

@pytest.mark.asyncio
async def test_middleware_registration(rest_server):
    middleware_calls = []
    
    @rest_server.middleware
    async def test_middleware(request, handler):
        middleware_calls.append("before")
        response = await handler(request)
        middleware_calls.append("after")
        return response
    
    async def test_handler(request):
        middleware_calls.append("handler")
        return web.json_response({"message": "Success"})
    
    await rest_server.register_route(
        path="/test",
        method="GET",
        handler=test_handler,
        middleware=["test_middleware"]
    )
    
    # Create test request
    request = Mock()
    request.method = "GET"
    request.path = "/test"
    
    await rest_server._handle_request(request)
    assert middleware_calls == ["before", "handler", "after"]

@pytest.mark.asyncio
async def test_cors_handling(rest_server):
    with patch('aiohttp.web.Application') as mock_app:
        mock_app_instance = Mock()
        mock_app.return_value = mock_app_instance
        
        rest_server.config.cors_enabled = True
        rest_server.config.cors_origins = ["http://localhost:3000"]
        
        await rest_server.setup()
        
        # Verify CORS middleware was added
        mock_app.assert_called_once()
        assert any(
            middleware.__name__ == "cors_middleware"
            for middleware in rest_server.middleware
        )

@pytest.mark.asyncio
async def test_error_handling(rest_server):
    async def error_handler(request):
        raise RestError(
            status=400,
            message="Bad Request",
            details={"field": "invalid"}
        )
    
    await rest_server.register_route(
        path="/error",
        method="GET",
        handler=error_handler
    )
    
    # Create test request
    request = Mock()
    request.method = "GET"
    request.path = "/error"
    
    response = await rest_server._handle_request(request)
    assert response.status == 400
    assert "message" in response.body

@pytest.mark.asyncio
async def test_request_validation(rest_server):
    validation_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name", "age"]
    }
    
    async def handler(request):
        return web.json_response({"message": "Success"})
    
    await rest_server.register_route(
        path="/validated",
        method="POST",
        handler=handler,
        validation_schema=validation_schema
    )
    
    # Test valid request
    valid_request = Mock()
    valid_request.method = "POST"
    valid_request.path = "/validated"
    valid_request.json = AsyncMock(
        return_value={"name": "test", "age": 25}
    )
    
    response = await rest_server._handle_request(valid_request)
    assert response.status == 200
    
    # Test invalid request
    invalid_request = Mock()
    invalid_request.method = "POST"
    invalid_request.path = "/validated"
    invalid_request.json = AsyncMock(
        return_value={"name": "test"}  # Missing required field
    )
    
    response = await rest_server._handle_request(invalid_request)
    assert response.status == 400

@pytest.mark.asyncio
async def test_rate_limiting(rest_server):
    rate_limit_config = {
        "requests_per_second": 2,
        "burst": 1
    }
    
    async def handler(request):
        return web.json_response({"message": "Success"})
    
    await rest_server.register_route(
        path="/limited",
        method="GET",
        handler=handler,
        rate_limit=rate_limit_config
    )
    
    # Make requests within limit
    request = Mock()
    request.method = "GET"
    request.path = "/limited"
    request.remote = "127.0.0.1"
    
    response1 = await rest_server._handle_request(request)
    response2 = await rest_server._handle_request(request)
    assert response1.status == 200
    assert response2.status == 200
    
    # Exceed rate limit
    response3 = await rest_server._handle_request(request)
    assert response3.status == 429

@pytest.mark.asyncio
async def test_compression(rest_server):
    async def handler(request):
        return web.json_response({"data": "x" * 1000})  # Large response
    
    await rest_server.register_route(
        path="/compressed",
        method="GET",
        handler=handler
    )
    
    request = Mock()
    request.method = "GET"
    request.path = "/compressed"
    request.headers = {"Accept-Encoding": "gzip"}
    
    response = await rest_server._handle_request(request)
    assert "Content-Encoding" in response.headers
    assert response.headers["Content-Encoding"] == "gzip"

@pytest.mark.asyncio
async def test_metrics_collection(rest_server):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        async def handler(request):
            return web.json_response({"message": "Success"})
        
        await rest_server.register_route(
            path="/metrics",
            method="GET",
            handler=handler
        )
        
        request = Mock()
        request.method = "GET"
        request.path = "/metrics"
        
        await rest_server._handle_request(request)
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_histogram.assert_called()

@pytest.mark.asyncio
async def test_health_check(rest_server):
    with patch.object(rest_server, '_check_health') as mock_health:
        mock_health.return_value = True
        
        request = Mock()
        request.method = "GET"
        request.path = "/health"
        
        response = await rest_server._handle_request(request)
        assert response.status == 200
        assert await response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_static_file_serving(rest_server):
    with patch('aiohttp.web.static') as mock_static:
        await rest_server.serve_static(
            prefix="/static",
            path="./static"
        )
        
        mock_static.assert_called_once()
        assert any(
            route.path.startswith("/static")
            for route in rest_server.routes
        )

@pytest.mark.asyncio
async def test_websocket_handling(rest_server):
    ws_messages = []
    
    async def ws_handler(ws):
        async for msg in ws:
            ws_messages.append(msg.data)
            await ws.send_str("Echo: " + msg.data)
    
    await rest_server.register_websocket(
        path="/ws",
        handler=ws_handler
    )
    
    # Mock WebSocket connection
    ws = AsyncMock()
    ws.__aiter__.return_value = ["test1", "test2"]
    
    request = Mock()
    request.method = "GET"
    request.path = "/ws"
    request.headers = {"Upgrade": "websocket"}
    
    await rest_server._handle_websocket(request, ws)
    
    assert len(ws_messages) == 2
    assert ws.send_str.call_count == 2

@pytest.mark.asyncio
async def test_graceful_shutdown(rest_server):
    with patch('aiohttp.web.Application') as mock_app:
        mock_app_instance = AsyncMock()
        mock_app.return_value = mock_app_instance
        
        await rest_server.start()
        
        # Simulate active connections
        active_requests = [
            asyncio.create_task(
                rest_server._handle_request(Mock())
            )
            for _ in range(3)
        ]
        
        # Start graceful shutdown
        shutdown_task = asyncio.create_task(
            rest_server.shutdown(grace=2.0)
        )
        
        # Wait for shutdown to complete
        await shutdown_task
        
        mock_app_instance.shutdown.assert_called_once()
        assert not rest_server.is_running