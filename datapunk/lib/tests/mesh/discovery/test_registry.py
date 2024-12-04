import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.discovery import (
    ServiceRegistry,
    RegistryConfig,
    ServiceRecord,
    RegistryError,
    ServiceState
)

@pytest.fixture
def registry_config():
    return RegistryConfig(
        ttl=30,  # 30 seconds
        cleanup_interval=5,
        max_services=100,
        health_check_interval=10
    )

@pytest.fixture
def service_registry(registry_config):
    return ServiceRegistry(config=registry_config)

@pytest.fixture
def sample_service():
    return ServiceRecord(
        id="test-service-1",
        name="test-service",
        host="localhost",
        port=8080,
        metadata={
            "version": "1.0.0",
            "environment": "test"
        }
    )

@pytest.mark.asyncio
async def test_registry_initialization(service_registry, registry_config):
    assert service_registry.config == registry_config
    assert len(service_registry.services) == 0
    assert not service_registry.is_closed

@pytest.mark.asyncio
async def test_service_registration(service_registry, sample_service):
    # Register service
    await service_registry.register(sample_service)
    
    # Verify registration
    assert sample_service.id in service_registry.services
    registered = service_registry.services[sample_service.id]
    assert registered.name == sample_service.name
    assert registered.state == ServiceState.ACTIVE

@pytest.mark.asyncio
async def test_service_deregistration(service_registry, sample_service):
    # Register and then deregister
    await service_registry.register(sample_service)
    await service_registry.deregister(sample_service.id)
    
    assert sample_service.id not in service_registry.services

@pytest.mark.asyncio
async def test_service_health_check(service_registry, sample_service):
    health_checks = []
    
    async def mock_health_check(service):
        health_checks.append(service)
        return True
    
    service_registry.health_checker = mock_health_check
    
    await service_registry.register(sample_service)
    await service_registry.check_health(sample_service.id)
    
    assert len(health_checks) == 1
    assert health_checks[0].id == sample_service.id

@pytest.mark.asyncio
async def test_service_ttl(service_registry):
    # Create service with short TTL
    service = ServiceRecord(
        id="test-service",
        name="test-service",
        host="localhost",
        port=8080,
        ttl=0.1  # 100ms TTL
    )
    
    await service_registry.register(service)
    assert service.id in service_registry.services
    
    # Wait for TTL expiration
    await asyncio.sleep(0.2)
    await service_registry.cleanup_expired()
    
    assert service.id not in service_registry.services

@pytest.mark.asyncio
async def test_service_heartbeat(service_registry, sample_service):
    await service_registry.register(sample_service)
    
    # Update heartbeat
    await service_registry.heartbeat(sample_service.id)
    
    service = service_registry.services[sample_service.id]
    assert (datetime.utcnow() - service.last_heartbeat).total_seconds() < 1

@pytest.mark.asyncio
async def test_service_query(service_registry):
    # Register multiple services
    services = [
        ServiceRecord(
            id=f"service-{i}",
            name="test-service",
            host="localhost",
            port=8080 + i,
            metadata={"version": f"1.{i}.0"}
        )
        for i in range(3)
    ]
    
    for service in services:
        await service_registry.register(service)
    
    # Query services
    results = await service_registry.query(
        name="test-service",
        metadata={"version": "1.1.0"}
    )
    
    assert len(results) == 1
    assert results[0].metadata["version"] == "1.1.0"

@pytest.mark.asyncio
async def test_service_state_transitions(service_registry, sample_service):
    await service_registry.register(sample_service)
    
    # Test state transitions
    await service_registry.set_service_state(
        sample_service.id,
        ServiceState.DEGRADED
    )
    assert service_registry.services[sample_service.id].state == ServiceState.DEGRADED
    
    await service_registry.set_service_state(
        sample_service.id,
        ServiceState.ACTIVE
    )
    assert service_registry.services[sample_service.id].state == ServiceState.ACTIVE

@pytest.mark.asyncio
async def test_concurrent_operations(service_registry):
    # Create multiple services
    services = [
        ServiceRecord(
            id=f"service-{i}",
            name="test-service",
            host="localhost",
            port=8080 + i
        )
        for i in range(5)
    ]
    
    # Register services concurrently
    await asyncio.gather(*[
        service_registry.register(service)
        for service in services
    ])
    
    assert len(service_registry.services) == 5

@pytest.mark.asyncio
async def test_service_updates(service_registry, sample_service):
    await service_registry.register(sample_service)
    
    # Update service metadata
    updated_metadata = {
        **sample_service.metadata,
        "updated": True
    }
    
    await service_registry.update_service(
        sample_service.id,
        metadata=updated_metadata
    )
    
    service = service_registry.services[sample_service.id]
    assert service.metadata["updated"] is True

@pytest.mark.asyncio
async def test_service_filtering(service_registry):
    # Register services with different tags
    services = [
        ServiceRecord(
            id=f"service-{i}",
            name="test-service",
            host="localhost",
            port=8080 + i,
            metadata={"environment": "prod" if i % 2 == 0 else "dev"}
        )
        for i in range(4)
    ]
    
    for service in services:
        await service_registry.register(service)
    
    # Filter services
    prod_services = await service_registry.filter_services(
        lambda s: s.metadata["environment"] == "prod"
    )
    
    assert len(prod_services) == 2
    assert all(s.metadata["environment"] == "prod" for s in prod_services)

@pytest.mark.asyncio
async def test_registry_events(service_registry, sample_service):
    events = []
    
    def event_handler(event_type, service):
        events.append((event_type, service))
    
    service_registry.on_service_event(event_handler)
    
    # Trigger events
    await service_registry.register(sample_service)
    await service_registry.deregister(sample_service.id)
    
    assert len(events) == 2
    assert events[0][0] == "registered"
    assert events[1][0] == "deregistered"

@pytest.mark.asyncio
async def test_registry_persistence(service_registry, sample_service):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        await service_registry.register(sample_service)
        
        await service_registry.save_state()
        mock_file.write.assert_called_once()
        
        await service_registry.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_registry_metrics(service_registry, sample_service):
    with patch('datapunk_shared.metrics.MetricsCollector') as mock_collector:
        await service_registry.register(sample_service)
        await service_registry.deregister(sample_service.id)
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_gauge.assert_called()

@pytest.mark.asyncio
async def test_cleanup(service_registry, sample_service):
    cleanup_called = False
    
    async def cleanup_handler():
        nonlocal cleanup_called
        cleanup_called = True
    
    service_registry.on_cleanup(cleanup_handler)
    
    await service_registry.register(sample_service)
    await service_registry.cleanup()
    
    assert cleanup_called
    assert len(service_registry.services) == 0 