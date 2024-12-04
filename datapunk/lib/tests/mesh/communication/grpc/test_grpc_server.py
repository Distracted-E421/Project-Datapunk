import pytest
import asyncio
import grpc
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.communication.grpc import (
    GrpcServer,
    ServerConfig,
    ServiceDefinition,
    GrpcError,
    StreamHandler
)

@pytest.fixture
def server_config():
    return ServerConfig(
        host="localhost",
        port=50051,
        max_workers=10,
        max_message_length=4 * 1024 * 1024,  # 4MB
        enable_reflection=True
    )

@pytest.fixture
def grpc_server(server_config):
    return GrpcServer(config=server_config)

@pytest.fixture
def sample_service():
    return ServiceDefinition(
        name="TestService",
        methods={
            "TestMethod": {
                "input_type": "TestRequest",
                "output_type": "TestResponse",
                "is_streaming": False
            },
            "TestStreamMethod": {
                "input_type": "TestRequest",
                "output_type": "TestResponse",
                "is_streaming": True
            }
        }
    )

@pytest.mark.asyncio
async def test_server_initialization(grpc_server, server_config):
    assert grpc_server.config == server_config
    assert not grpc_server.is_running
    assert len(grpc_server.services) == 0

@pytest.mark.asyncio
async def test_service_registration(grpc_server, sample_service):
    await grpc_server.register_service(sample_service)
    assert sample_service.name in grpc_server.services

@pytest.mark.asyncio
async def test_server_start_stop(grpc_server):
    with patch('grpc.aio.server') as mock_server:
        mock_server_instance = AsyncMock()
        mock_server.return_value = mock_server_instance
        
        await grpc_server.start()
        mock_server_instance.start.assert_called_once()
        assert grpc_server.is_running
        
        await grpc_server.stop()
        mock_server_instance.stop.assert_called_once()
        assert not grpc_server.is_running

@pytest.mark.asyncio
async def test_request_handling(grpc_server, sample_service):
    # Mock request handler
    async def handler(request):
        return {"message": "Success"}
    
    await grpc_server.register_service(sample_service)
    await grpc_server.add_method_handler(
        service_name=sample_service.name,
        method_name="TestMethod",
        handler=handler
    )
    
    # Simulate request
    request = {"data": "test"}
    response = await grpc_server.handle_request(
        service_name=sample_service.name,
        method_name="TestMethod",
        request=request
    )
    
    assert response["message"] == "Success"

@pytest.mark.asyncio
async def test_streaming_request(grpc_server, sample_service):
    # Mock streaming handler
    async def stream_handler(request_iterator):
        async for request in request_iterator:
            yield {"message": f"Processed {request['data']}"}
    
    await grpc_server.register_service(sample_service)
    await grpc_server.add_stream_handler(
        service_name=sample_service.name,
        method_name="TestStreamMethod",
        handler=stream_handler
    )
    
    # Simulate streaming request
    async def request_iterator():
        for i in range(3):
            yield {"data": f"item{i}"}
    
    responses = []
    async for response in grpc_server.handle_stream(
        service_name=sample_service.name,
        method_name="TestStreamMethod",
        request_iterator=request_iterator()
    ):
        responses.append(response)
    
    assert len(responses) == 3
    assert all("Processed" in r["message"] for r in responses)

@pytest.mark.asyncio
async def test_error_handling(grpc_server, sample_service):
    # Mock handler that raises error
    async def error_handler(request):
        raise GrpcError(
            code=grpc.StatusCode.INVALID_ARGUMENT,
            details="Invalid request"
        )
    
    await grpc_server.register_service(sample_service)
    await grpc_server.add_method_handler(
        service_name=sample_service.name,
        method_name="TestMethod",
        handler=error_handler
    )
    
    with pytest.raises(GrpcError) as exc_info:
        await grpc_server.handle_request(
            service_name=sample_service.name,
            method_name="TestMethod",
            request={"data": "invalid"}
        )
    
    assert exc_info.value.code == grpc.StatusCode.INVALID_ARGUMENT

@pytest.mark.asyncio
async def test_middleware_execution(grpc_server):
    middleware_calls = []
    
    @grpc_server.middleware
    async def test_middleware(request, context, next_handler):
        middleware_calls.append("before")
        response = await next_handler(request, context)
        middleware_calls.append("after")
        return response
    
    async def handler(request):
        middleware_calls.append("handler")
        return {"message": "Success"}
    
    await grpc_server.register_service(sample_service)
    await grpc_server.add_method_handler(
        service_name=sample_service.name,
        method_name="TestMethod",
        handler=handler
    )
    
    await grpc_server.handle_request(
        service_name=sample_service.name,
        method_name="TestMethod",
        request={"data": "test"}
    )
    
    assert middleware_calls == ["before", "handler", "after"]

@pytest.mark.asyncio
async def test_interceptor_chain(grpc_server):
    interceptor_calls = []
    
    class TestInterceptor(grpc.aio.ServerInterceptor):
        async def intercept_service(self, continuation, handler_call_details):
            interceptor_calls.append("intercept")
            return await continuation(handler_call_details)
    
    await grpc_server.add_interceptor(TestInterceptor())
    
    with patch('grpc.aio.server') as mock_server:
        mock_server_instance = AsyncMock()
        mock_server.return_value = mock_server_instance
        
        await grpc_server.start()
        assert len(grpc_server.interceptors) == 1

@pytest.mark.asyncio
async def test_service_reflection(grpc_server, sample_service):
    await grpc_server.register_service(sample_service)
    
    reflection_data = await grpc_server.get_service_reflection()
    assert sample_service.name in reflection_data
    assert "TestMethod" in reflection_data[sample_service.name]["methods"]

@pytest.mark.asyncio
async def test_concurrent_requests(grpc_server, sample_service):
    request_count = 0
    
    async def handler(request):
        nonlocal request_count
        request_count += 1
        await asyncio.sleep(0.1)  # Simulate work
        return {"count": request_count}
    
    await grpc_server.register_service(sample_service)
    await grpc_server.add_method_handler(
        service_name=sample_service.name,
        method_name="TestMethod",
        handler=handler
    )
    
    # Make concurrent requests
    requests = [
        grpc_server.handle_request(
            service_name=sample_service.name,
            method_name="TestMethod",
            request={"data": f"test{i}"}
        )
        for i in range(5)
    ]
    
    responses = await asyncio.gather(*requests)
    assert len(responses) == 5
    assert all(isinstance(r["count"], int) for r in responses)

@pytest.mark.asyncio
async def test_server_metrics(grpc_server):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        await grpc_server.start()
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_gauge.assert_called()

@pytest.mark.asyncio
async def test_health_check(grpc_server):
    with patch.object(grpc_server, '_check_health') as mock_health:
        mock_health.return_value = True
        
        is_healthy = await grpc_server.check_health()
        assert is_healthy
        mock_health.assert_called_once()

@pytest.mark.asyncio
async def test_graceful_shutdown(grpc_server):
    with patch('grpc.aio.server') as mock_server:
        mock_server_instance = AsyncMock()
        mock_server.return_value = mock_server_instance
        
        await grpc_server.start()
        
        # Simulate active requests
        active_requests = [
            asyncio.create_task(
                grpc_server.handle_request(
                    service_name="TestService",
                    method_name="TestMethod",
                    request={"data": "test"}
                )
            )
            for _ in range(3)
        ]
        
        # Start graceful shutdown
        shutdown_task = asyncio.create_task(grpc_server.shutdown(grace=2.0))
        
        # Wait for shutdown to complete
        await shutdown_task
        
        mock_server_instance.stop.assert_called_once()
        assert not grpc_server.is_running 