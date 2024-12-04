import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from datapunk_shared.mesh.service import (
    MeshService,
    ServiceConfig,
    ServiceState,
    ServiceError,
    HealthStatus
)

@pytest.fixture
def service_config():
    return ServiceConfig(
        name="test_service",
        version="1.0.0",
        port=8080,
        health_check_interval=1
    )

@pytest.fixture
def mesh_service(service_config):
    return MeshService(config=service_config)

@pytest.mark.asyncio
async def test_service_initialization(mesh_service, service_config):
    assert mesh_service.config == service_config
    assert mesh_service.state == ServiceState.INITIALIZED
    assert mesh_service.health_status == HealthStatus.UNKNOWN

@pytest.mark.asyncio
async def test_service_startup():
    with patch('aiohttp.web.Application') as mock_app:
        service = MeshService(ServiceConfig(name="test", port=8080))
        await service.start()
        
        assert service.state == ServiceState.RUNNING
        mock_app.return_value.startup.assert_called_once()

@pytest.mark.asyncio
async def test_service_shutdown(mesh_service):
    await mesh_service.start()
    await mesh_service.stop()
    
    assert mesh_service.state == ServiceState.STOPPED
    assert not mesh_service.is_running

@pytest.mark.asyncio
async def test_health_check_execution(mesh_service):
    # Mock health check dependencies
    mock_checker = AsyncMock()
    mock_checker.check_health.return_value = True
    mesh_service.health_checker = mock_checker
    
    await mesh_service.start()
    health_status = await mesh_service.check_health()
    
    assert health_status == HealthStatus.HEALTHY
    mock_checker.check_health.assert_called_once()

@pytest.mark.asyncio
async def test_metrics_reporting(mesh_service):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        await mesh_service.start()
        await mesh_service.report_metrics()
        
        mock_collector.return_value.collect.assert_called_once()

@pytest.mark.asyncio
async def test_service_registration():
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        service = MeshService(ServiceConfig(name="test", port=8080))
        await service.start()
        
        mock_registry.return_value.register.assert_called_once()
        assert service.is_registered

@pytest.mark.asyncio
async def test_service_deregistration(mesh_service):
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        await mesh_service.start()
        await mesh_service.stop()
        
        mock_registry.return_value.deregister.assert_called_once()
        assert not mesh_service.is_registered

@pytest.mark.asyncio
async def test_service_endpoint_registration(mesh_service):
    # Test endpoint registration
    @mesh_service.endpoint("/test")
    async def test_endpoint():
        return {"status": "ok"}
    
    assert "/test" in mesh_service.endpoints
    assert mesh_service.endpoints["/test"] == test_endpoint

@pytest.mark.asyncio
async def test_service_middleware_chain(mesh_service):
    middleware_calls = []
    
    @mesh_service.middleware
    async def test_middleware(request, handler):
        middleware_calls.append("before")
        response = await handler(request)
        middleware_calls.append("after")
        return response
    
    assert len(mesh_service.middleware_stack) == 1
    assert "test_middleware" in str(mesh_service.middleware_stack[0])

@pytest.mark.asyncio
async def test_service_error_handling(mesh_service):
    error_handled = False
    
    @mesh_service.error_handler(ServiceError)
    async def handle_error(error):
        nonlocal error_handled
        error_handled = True
        return {"error": str(error)}
    
    # Simulate error in endpoint
    @mesh_service.endpoint("/error")
    async def error_endpoint():
        raise ServiceError("Test error")
    
    response = await mesh_service._handle_request(
        Mock(path="/error", method="GET")
    )
    
    assert error_handled
    assert "error" in response

@pytest.mark.asyncio
async def test_service_configuration_validation():
    # Test invalid configuration
    with pytest.raises(ServiceError):
        ServiceConfig(
            name="",  # Invalid empty name
            port=-1,  # Invalid port
            health_check_interval=-1  # Invalid interval
        )

@pytest.mark.asyncio
async def test_service_state_transitions(mesh_service):
    # Test state transition sequence
    assert mesh_service.state == ServiceState.INITIALIZED
    
    await mesh_service.start()
    assert mesh_service.state == ServiceState.RUNNING
    
    await mesh_service.pause()
    assert mesh_service.state == ServiceState.PAUSED
    
    await mesh_service.resume()
    assert mesh_service.state == ServiceState.RUNNING
    
    await mesh_service.stop()
    assert mesh_service.state == ServiceState.STOPPED

@pytest.mark.asyncio
async def test_service_dependency_injection(mesh_service):
    # Test dependency registration and injection
    test_dependency = Mock()
    mesh_service.register_dependency("test", test_dependency)
    
    @mesh_service.endpoint("/test")
    async def test_endpoint(test=mesh_service.inject("test")):
        test.some_method()
        return {"status": "ok"}
    
    await mesh_service._handle_request(
        Mock(path="/test", method="GET")
    )
    
    test_dependency.some_method.assert_called_once()

@pytest.mark.asyncio
async def test_service_graceful_shutdown(mesh_service):
    shutdown_complete = False
    
    @mesh_service.on_shutdown
    async def cleanup():
        nonlocal shutdown_complete
        await asyncio.sleep(0.1)  # Simulate cleanup
        shutdown_complete = True
    
    await mesh_service.start()
    await mesh_service.stop()
    
    assert shutdown_complete 