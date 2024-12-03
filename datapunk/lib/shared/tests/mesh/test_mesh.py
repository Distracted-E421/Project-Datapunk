import pytest
from unittest.mock import Mock, patch
from datapunk_shared.mesh.mesh import (
    ServiceMesh,
    MeshConfig,
    ServiceInstance,
    MeshError
)

@pytest.fixture
def mesh_config():
    return MeshConfig(
        service_name="test_service",
        discovery_endpoint="http://discovery:8500",
        health_check_interval=5,
        metrics_enabled=True
    )

@pytest.fixture
def service_mesh(mesh_config):
    return ServiceMesh(config=mesh_config)

def test_mesh_initialization(service_mesh, mesh_config):
    assert service_mesh.config == mesh_config
    assert service_mesh.is_running == False
    assert len(service_mesh.registered_services) == 0

@pytest.mark.asyncio
async def test_service_registration():
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mesh = ServiceMesh(MeshConfig(service_name="test"))
        instance = ServiceInstance(
            id="test_1",
            name="test_service",
            address="localhost",
            port=8080
        )
        
        await mesh.register_service(instance)
        mock_registry.register.assert_called_once_with(instance)

@pytest.mark.asyncio
async def test_service_discovery():
    with patch('datapunk_shared.mesh.discovery.ServiceDiscovery') as mock_discovery:
        mesh = ServiceMesh(MeshConfig(service_name="test"))
        mock_discovery.discover.return_value = [
            ServiceInstance(id="1", name="service1", address="host1", port=8080),
            ServiceInstance(id="2", name="service1", address="host2", port=8080)
        ]
        
        instances = await mesh.discover_service("service1")
        assert len(instances) == 2
        mock_discovery.discover.assert_called_once_with("service1")

@pytest.mark.asyncio
async def test_health_check_integration():
    with patch('datapunk_shared.mesh.health.HealthChecker') as mock_checker:
        mesh = ServiceMesh(MeshConfig(
            service_name="test",
            health_check_interval=1
        ))
        
        await mesh.start_health_checks()
        mock_checker.start.assert_called_once()
        
        await mesh.stop_health_checks()
        mock_checker.stop.assert_called_once()

@pytest.mark.asyncio
async def test_metrics_collection():
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        mesh = ServiceMesh(MeshConfig(
            service_name="test",
            metrics_enabled=True
        ))
        
        await mesh.start_metrics_collection()
        mock_collector.start.assert_called_once()
        
        await mesh.collect_metrics()
        mock_collector.collect.assert_called_once()

def test_mesh_configuration_validation():
    # Test invalid configuration
    with pytest.raises(MeshError):
        MeshConfig(
            service_name="",  # Invalid empty name
            discovery_endpoint="invalid-url",
            health_check_interval=-1  # Invalid negative interval
        )

@pytest.mark.asyncio
async def test_service_deregistration():
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mesh = ServiceMesh(MeshConfig(service_name="test"))
        instance = ServiceInstance(
            id="test_1",
            name="test_service",
            address="localhost",
            port=8080
        )
        
        await mesh.register_service(instance)
        await mesh.deregister_service(instance)
        mock_registry.deregister.assert_called_once_with(instance)

@pytest.mark.asyncio
async def test_mesh_shutdown():
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mesh = ServiceMesh(MeshConfig(service_name="test"))
        
        # Register some services
        instances = [
            ServiceInstance(id=f"test_{i}", name="test", address="localhost", port=8080)
            for i in range(3)
        ]
        for instance in instances:
            await mesh.register_service(instance)
        
        await mesh.shutdown()
        assert mock_registry.deregister.call_count == len(instances)
        assert mesh.is_running == False

@pytest.mark.asyncio
async def test_service_health_status():
    with patch('datapunk_shared.mesh.health.HealthChecker') as mock_checker:
        mesh = ServiceMesh(MeshConfig(service_name="test"))
        instance = ServiceInstance(
            id="test_1",
            name="test_service",
            address="localhost",
            port=8080
        )
        
        mock_checker.check_health.return_value = True
        assert await mesh.check_service_health(instance)
        
        mock_checker.check_health.return_value = False
        assert not await mesh.check_service_health(instance)

@pytest.mark.asyncio
async def test_mesh_error_handling():
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mesh = ServiceMesh(MeshConfig(service_name="test"))
        mock_registry.register.side_effect = Exception("Network error")
        
        with pytest.raises(MeshError):
            await mesh.register_service(
                ServiceInstance(id="1", name="test", address="localhost", port=8080)
            ) 