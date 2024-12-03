import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from datapunk_shared.mesh.discovery.metadata import (
    MetadataConfig,
    MetadataIndex,
    MetadataManager,
    ServiceRegistration,
    ServiceMetadata
)
from datapunk_shared.cache import CacheClient

@pytest.fixture
def mock_cache():
    cache = Mock(spec=CacheClient)
    cache.get = AsyncMock()
    cache.set = AsyncMock()
    return cache

@pytest.fixture
def metadata_config():
    return MetadataConfig(
        cache_ttl=300,
        max_tags=50,
        max_tag_length=100,
        enable_validation=True,
        enable_caching=True
    )

@pytest.fixture
def metadata_manager(metadata_config, mock_cache):
    return MetadataManager(metadata_config, mock_cache)

@pytest.fixture
def sample_service():
    return ServiceRegistration(
        id="test-service-1",
        service_name="test-service",
        host="192.168.1.10",
        port=8080,
        metadata=ServiceMetadata(
            version="1.0.0",
            environment="prod",
            region="us-west",
            tags={
                "team": "platform",
                "tier": "backend"
            }
        )
    )

@pytest.mark.asyncio
async def test_update_metadata_basic(metadata_manager, sample_service):
    """Test basic metadata update functionality"""
    new_metadata = ServiceMetadata(
        version="1.1.0",
        environment="staging",
        region="us-east",
        tags={
            "team": "platform",
            "tier": "backend",
            "feature": "new"
        }
    )
    
    success = await metadata_manager.update_metadata(sample_service, new_metadata)
    assert success
    
    # Query by new metadata
    services = await metadata_manager.query_services(
        tags={"feature": "new"},
        version="1.1.0",
        environment="staging",
        region="us-east"
    )
    
    assert len(services) == 1
    assert sample_service.id in services

@pytest.mark.asyncio
async def test_metadata_validation(metadata_manager, sample_service):
    """Test metadata validation rules"""
    # Test with invalid tag count
    invalid_metadata = ServiceMetadata(
        version="1.0.0",
        environment="prod",
        region="us-west",
        tags={f"tag{i}": "value" for i in range(51)}  # Exceeds max_tags
    )
    
    with pytest.raises(ValueError, match="Too many tags"):
        await metadata_manager.update_metadata(sample_service, invalid_metadata)
    
    # Test with invalid tag length
    invalid_metadata = ServiceMetadata(
        version="1.0.0",
        environment="prod",
        region="us-west",
        tags={"key": "x" * 101}  # Exceeds max_tag_length
    )
    
    with pytest.raises(ValueError, match="Tag value too long"):
        await metadata_manager.update_metadata(sample_service, invalid_metadata)
    
    # Test with missing required fields
    invalid_metadata = ServiceMetadata(
        version="",  # Empty version
        environment="prod",
        region="us-west"
    )
    
    with pytest.raises(ValueError, match="Version is required"):
        await metadata_manager.update_metadata(sample_service, invalid_metadata)

@pytest.mark.asyncio
async def test_query_services_by_tags(metadata_manager, sample_service):
    """Test querying services by tags"""
    # Update metadata first
    await metadata_manager.update_metadata(sample_service, sample_service.metadata)
    
    # Query by single tag
    services = await metadata_manager.query_services(
        tags={"team": "platform"}
    )
    assert len(services) == 1
    assert sample_service.id in services
    
    # Query by multiple tags
    services = await metadata_manager.query_services(
        tags={
            "team": "platform",
            "tier": "backend"
        }
    )
    assert len(services) == 1
    assert sample_service.id in services
    
    # Query by non-existent tag
    services = await metadata_manager.query_services(
        tags={"nonexistent": "value"}
    )
    assert len(services) == 0

@pytest.mark.asyncio
async def test_query_services_by_version(metadata_manager, sample_service):
    """Test querying services by version"""
    await metadata_manager.update_metadata(sample_service, sample_service.metadata)
    
    # Query by exact version
    services = await metadata_manager.query_services(
        version="1.0.0"
    )
    assert len(services) == 1
    assert sample_service.id in services
    
    # Query by non-existent version
    services = await metadata_manager.query_services(
        version="2.0.0"
    )
    assert len(services) == 0

@pytest.mark.asyncio
async def test_query_services_by_environment(metadata_manager, sample_service):
    """Test querying services by environment"""
    await metadata_manager.update_metadata(sample_service, sample_service.metadata)
    
    # Query by environment
    services = await metadata_manager.query_services(
        environment="prod"
    )
    assert len(services) == 1
    assert sample_service.id in services
    
    # Query by non-existent environment
    services = await metadata_manager.query_services(
        environment="dev"
    )
    assert len(services) == 0

@pytest.mark.asyncio
async def test_query_services_by_region(metadata_manager, sample_service):
    """Test querying services by region"""
    await metadata_manager.update_metadata(sample_service, sample_service.metadata)
    
    # Query by region
    services = await metadata_manager.query_services(
        region="us-west"
    )
    assert len(services) == 1
    assert sample_service.id in services
    
    # Query by non-existent region
    services = await metadata_manager.query_services(
        region="eu-west"
    )
    assert len(services) == 0

@pytest.mark.asyncio
async def test_metadata_caching(metadata_manager, sample_service, mock_cache):
    """Test metadata caching functionality"""
    await metadata_manager.update_metadata(sample_service, sample_service.metadata)
    
    # Verify cache was updated
    mock_cache.set.assert_called_once()
    call_args = mock_cache.set.call_args[0]
    assert call_args[0] == f"metadata:{sample_service.id}"
    assert isinstance(call_args[1], ServiceMetadata)
    
    # Update with caching disabled
    metadata_manager.config.enable_caching = False
    mock_cache.set.reset_mock()
    
    await metadata_manager.update_metadata(sample_service, sample_service.metadata)
    mock_cache.set.assert_not_called()

@pytest.mark.asyncio
async def test_metadata_stats(metadata_manager, sample_service):
    """Test metadata statistics collection"""
    # Add some metadata
    await metadata_manager.update_metadata(sample_service, sample_service.metadata)
    
    # Get stats
    stats = await metadata_manager.get_metadata_stats()
    
    assert stats["total_services"] == 1
    assert stats["total_versions"] == 1
    assert stats["total_environments"] == 1
    assert stats["total_regions"] == 1
    assert stats["total_tags"] == 2  # platform and backend
    assert isinstance(stats["last_update"], str)

@pytest.mark.asyncio
async def test_multiple_services_metadata(metadata_manager):
    """Test metadata management with multiple services"""
    services = [
        ServiceRegistration(
            id=f"service-{i}",
            service_name=f"service-{i}",
            host=f"192.168.1.{i}",
            port=8080,
            metadata=ServiceMetadata(
                version=f"1.0.{i}",
                environment="prod" if i % 2 == 0 else "staging",
                region="us-west" if i < 5 else "us-east",
                tags={
                    "team": f"team-{i % 3}",
                    "tier": "backend" if i % 2 == 0 else "frontend"
                }
            )
        ) for i in range(10)
    ]
    
    # Update metadata for all services
    for service in services:
        await metadata_manager.update_metadata(service, service.metadata)
    
    # Query by team
    team0_services = await metadata_manager.query_services(
        tags={"team": "team-0"}
    )
    assert len(team0_services) == 4  # Services 0, 3, 6, 9
    
    # Query by environment and tier
    prod_backend = await metadata_manager.query_services(
        environment="prod",
        tags={"tier": "backend"}
    )
    assert len(prod_backend) == 5  # Even-numbered services
    
    # Query by region
    east_services = await metadata_manager.query_services(
        region="us-east"
    )
    assert len(east_services) == 5  # Services 5-9 