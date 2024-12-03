import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datapunk_shared.mesh.service_discovery import (
    ServiceDiscovery,
    ServiceRegistry,
    DiscoveryConfig,
    ServiceInstance,
    DiscoveryError
)

@pytest.fixture
def discovery_config():
    return DiscoveryConfig(
        endpoint="http://discovery:8500",
        refresh_interval=5,
        ttl_seconds=30
    )

@pytest.fixture
def service_discovery(discovery_config):
    return ServiceDiscovery(config=discovery_config)

@pytest.fixture
def sample_service():
    return ServiceInstance(
        id="test_1",
        name="test_service",
        address="localhost",
        port=8080,
        metadata={"version": "1.0.0"}
    )

@pytest.mark.asyncio
async def test_service_registration(service_discovery, sample_service):
    with patch('aiohttp.ClientSession.put') as mock_put:
        mock_put.return_value.__aenter__.return_value.status = 200
        
        await service_discovery.register(sample_service)
        mock_put.assert_called_once()
        assert sample_service in service_discovery.registered_services

@pytest.mark.asyncio
async def test_service_deregistration(service_discovery, sample_service):
    with patch('aiohttp.ClientSession.delete') as mock_delete:
        mock_delete.return_value.__aenter__.return_value.status = 200
        
        # First register the service
        service_discovery.registered_services.add(sample_service)
        
        await service_discovery.deregister(sample_service)
        mock_delete.assert_called_once()
        assert sample_service not in service_discovery.registered_services

@pytest.mark.asyncio
async def test_service_discovery_query(service_discovery):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "services": [
                {
                    "id": "service1_1",
                    "name": "service1",
                    "address": "host1",
                    "port": 8080
                },
                {
                    "id": "service1_2",
                    "name": "service1",
                    "address": "host2",
                    "port": 8080
                }
            ]
        }
        mock_get.return_value.__aenter__.return_value = mock_response
        
        services = await service_discovery.discover("service1")
        assert len(services) == 2
        assert all(s.name == "service1" for s in services)

@pytest.mark.asyncio
async def test_service_health_check(service_discovery, sample_service):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        
        is_healthy = await service_discovery.check_health(sample_service)
        assert is_healthy
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_service_metadata_update(service_discovery, sample_service):
    with patch('aiohttp.ClientSession.put') as mock_put:
        mock_put.return_value.__aenter__.return_value.status = 200
        
        new_metadata = {"version": "1.1.0", "region": "us-west"}
        await service_discovery.update_metadata(sample_service, new_metadata)
        
        mock_put.assert_called_once()
        assert sample_service.metadata == new_metadata

@pytest.mark.asyncio
async def test_service_discovery_caching(service_discovery):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "services": [{"id": "1", "name": "service1", "address": "host1", "port": 8080}]
        }
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # First call should hit the API
        await service_discovery.discover("service1")
        assert mock_get.call_count == 1
        
        # Second call within cache TTL should use cached result
        await service_discovery.discover("service1")
        assert mock_get.call_count == 1

@pytest.mark.asyncio
async def test_service_discovery_error_handling(service_discovery, sample_service):
    with patch('aiohttp.ClientSession.put') as mock_put:
        mock_put.return_value.__aenter__.return_value.status = 500
        
        with pytest.raises(DiscoveryError):
            await service_discovery.register(sample_service)

@pytest.mark.asyncio
async def test_service_discovery_refresh(service_discovery):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"services": []}
        mock_get.return_value.__aenter__.return_value = mock_response
        
        await service_discovery.start_refresh()
        await asyncio.sleep(0.1)  # Allow refresh to run
        await service_discovery.stop_refresh()
        
        assert mock_get.called

@pytest.mark.asyncio
async def test_service_ttl_renewal(service_discovery, sample_service):
    with patch('aiohttp.ClientSession.put') as mock_put:
        mock_put.return_value.__aenter__.return_value.status = 200
        
        await service_discovery.register(sample_service)
        await service_discovery.renew_ttl(sample_service)
        
        assert mock_put.call_count == 2  # One for register, one for renewal

@pytest.mark.asyncio
async def test_service_discovery_cleanup(service_discovery, sample_service):
    with patch('aiohttp.ClientSession.delete') as mock_delete:
        mock_delete.return_value.__aenter__.return_value.status = 200
        
        service_discovery.registered_services.add(sample_service)
        await service_discovery.cleanup()
        
        assert len(service_discovery.registered_services) == 0
        assert mock_delete.called 