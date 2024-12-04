import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.auth import (
    AuthDiscoveryIntegration,
    DiscoveryConfig,
    ServiceRegistration,
    AuthProvider,
    DiscoveryEvent
)

@pytest.fixture
def discovery_config():
    return DiscoveryConfig(
        sync_interval=30,  # 30 seconds
        ttl=300,  # 5 minutes
        retry_attempts=3,
        retry_delay=5
    )

@pytest.fixture
def auth_discovery(discovery_config):
    return AuthDiscoveryIntegration(config=discovery_config)

@pytest.fixture
def sample_services():
    return [
        ServiceRegistration(
            service_id="auth-service-1",
            host="auth1.example.com",
            port=8443,
            provider=AuthProvider.LOCAL,
            metadata={"region": "us-west"}
        ),
        ServiceRegistration(
            service_id="auth-service-2",
            host="auth2.example.com",
            port=8443,
            provider=AuthProvider.OAUTH,
            metadata={"region": "us-east"}
        )
    ]

@pytest.mark.asyncio
async def test_discovery_initialization(auth_discovery, discovery_config):
    assert auth_discovery.config == discovery_config
    assert auth_discovery.is_initialized
    assert len(auth_discovery.registered_services) == 0

@pytest.mark.asyncio
async def test_service_registration(auth_discovery, sample_services):
    for service in sample_services:
        await auth_discovery.register_service(service)
    
    assert len(auth_discovery.registered_services) == len(sample_services)
    assert all(s.service_id in auth_discovery.registered_services 
              for s in sample_services)

@pytest.mark.asyncio
async def test_service_discovery(auth_discovery, sample_services):
    # Register services
    for service in sample_services:
        await auth_discovery.register_service(service)
    
    # Discover services by provider
    oauth_services = await auth_discovery.discover_services(
        provider=AuthProvider.OAUTH
    )
    
    assert len(oauth_services) == 1
    assert oauth_services[0].provider == AuthProvider.OAUTH

@pytest.mark.asyncio
async def test_service_health_check(auth_discovery, sample_services):
    service = sample_services[0]
    await auth_discovery.register_service(service)
    
    # Mock health check response
    with patch.object(auth_discovery, '_check_service_health') as mock_health:
        mock_health.return_value = True
        
        is_healthy = await auth_discovery.check_service_health(
            service.service_id
        )
        
        assert is_healthy
        mock_health.assert_called_once_with(service)

@pytest.mark.asyncio
async def test_service_sync(auth_discovery):
    with patch.object(auth_discovery, '_sync_with_registry') as mock_sync:
        mock_sync.return_value = True
        
        # Trigger sync
        success = await auth_discovery.sync_services()
        
        assert success
        mock_sync.assert_called_once()

@pytest.mark.asyncio
async def test_service_updates(auth_discovery, sample_services):
    service = sample_services[0]
    await auth_discovery.register_service(service)
    
    # Update service
    updated_service = ServiceRegistration(
        service_id=service.service_id,
        host="new-auth1.example.com",
        port=9443,
        provider=service.provider,
        metadata={"region": "us-west", "version": "2.0"}
    )
    
    await auth_discovery.update_service(updated_service)
    
    stored_service = auth_discovery.registered_services[service.service_id]
    assert stored_service.host == "new-auth1.example.com"
    assert stored_service.port == 9443

@pytest.mark.asyncio
async def test_service_deregistration(auth_discovery, sample_services):
    service = sample_services[0]
    await auth_discovery.register_service(service)
    
    # Deregister service
    await auth_discovery.deregister_service(service.service_id)
    
    assert service.service_id not in auth_discovery.registered_services

@pytest.mark.asyncio
async def test_discovery_events(auth_discovery, sample_services):
    events = []
    
    def event_handler(event: DiscoveryEvent):
        events.append(event)
    
    auth_discovery.on_discovery_event(event_handler)
    
    # Register a service
    await auth_discovery.register_service(sample_services[0])
    
    assert len(events) == 1
    assert events[0].event_type == "service_registered"

@pytest.mark.asyncio
async def test_service_resolution(auth_discovery, sample_services):
    for service in sample_services:
        await auth_discovery.register_service(service)
    
    # Resolve service by region
    resolved = await auth_discovery.resolve_services(
        criteria={"region": "us-west"}
    )
    
    assert len(resolved) == 1
    assert resolved[0].metadata["region"] == "us-west"

@pytest.mark.asyncio
async def test_concurrent_registration(auth_discovery):
    # Generate multiple services
    services = [
        ServiceRegistration(
            service_id=f"auth-service-{i}",
            host=f"auth{i}.example.com",
            port=8443,
            provider=AuthProvider.LOCAL,
            metadata={}
        )
        for i in range(100)
    ]
    
    # Register services concurrently
    await asyncio.gather(*[
        auth_discovery.register_service(service)
        for service in services
    ])
    
    assert len(auth_discovery.registered_services) == 100

@pytest.mark.asyncio
async def test_discovery_persistence(auth_discovery):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        await auth_discovery.save_state()
        mock_file.write.assert_called_once()
        
        await auth_discovery.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_service_ttl(auth_discovery, sample_services):
    service = sample_services[0]
    
    # Register service with TTL
    await auth_discovery.register_service(
        service,
        ttl=1  # 1 second TTL
    )
    
    # Wait for TTL to expire
    await asyncio.sleep(1.1)
    
    # Service should be automatically deregistered
    assert service.service_id not in auth_discovery.registered_services

@pytest.mark.asyncio
async def test_provider_failover(auth_discovery, sample_services):
    primary = sample_services[0]
    backup = sample_services[1]
    
    await auth_discovery.register_service(primary)
    await auth_discovery.register_service(backup)
    
    # Simulate primary failure
    with patch.object(auth_discovery, '_check_service_health') as mock_health:
        mock_health.side_effect = lambda s: s.service_id != primary.service_id
        
        # Get available service
        available = await auth_discovery.get_available_service(
            provider=primary.provider
        )
        
        assert available.service_id == backup.service_id

@pytest.mark.asyncio
async def test_service_metrics(auth_discovery, sample_services):
    for service in sample_services:
        await auth_discovery.register_service(service)
    
    # Get discovery metrics
    metrics = await auth_discovery.get_discovery_metrics()
    
    assert "total_services" in metrics
    assert "services_per_provider" in metrics
    assert metrics["total_services"] == len(sample_services)

@pytest.mark.asyncio
async def test_discovery_retry(auth_discovery):
    with patch.object(auth_discovery, '_sync_with_registry') as mock_sync:
        # Fail first two attempts, succeed on third
        mock_sync.side_effect = [False, False, True]
        
        success = await auth_discovery.sync_services()
        
        assert success
        assert mock_sync.call_count == 3

@pytest.mark.asyncio
async def test_service_validation(auth_discovery):
    # Try to register invalid service
    invalid_service = ServiceRegistration(
        service_id="",  # Invalid empty ID
        host="auth.example.com",
        port=8443,
        provider=AuthProvider.LOCAL,
        metadata={}
    )
    
    with pytest.raises(ValueError):
        await auth_discovery.register_service(invalid_service) 