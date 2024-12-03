import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.discovery import (
    ServiceResolver,
    ResolverConfig,
    ServiceEndpoint,
    ResolutionError,
    LoadBalancingStrategy
)

@pytest.fixture
def resolver_config():
    return ResolverConfig(
        cache_ttl=30,  # 30 seconds
        refresh_interval=5,
        max_retries=3,
        retry_delay=0.1,
        load_balancing="round_robin"
    )

@pytest.fixture
def service_resolver(resolver_config):
    return ServiceResolver(config=resolver_config)

@pytest.fixture
def sample_endpoints():
    return [
        ServiceEndpoint(
            id=f"endpoint-{i}",
            service="test-service",
            host=f"host-{i}",
            port=8080 + i,
            metadata={"region": "us-west"}
        )
        for i in range(3)
    ]

@pytest.mark.asyncio
async def test_resolver_initialization(service_resolver, resolver_config):
    assert service_resolver.config == resolver_config
    assert len(service_resolver.cache) == 0
    assert not service_resolver.is_closed

@pytest.mark.asyncio
async def test_service_resolution(service_resolver, sample_endpoints):
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mock_registry.return_value.query.return_value = sample_endpoints
        
        endpoint = await service_resolver.resolve("test-service")
        
        assert endpoint in sample_endpoints
        assert endpoint.service == "test-service"

@pytest.mark.asyncio
async def test_resolution_caching(service_resolver, sample_endpoints):
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mock_registry.return_value.query.return_value = sample_endpoints
        
        # First resolution (should query registry)
        await service_resolver.resolve("test-service")
        assert mock_registry.return_value.query.call_count == 1
        
        # Second resolution (should use cache)
        await service_resolver.resolve("test-service")
        assert mock_registry.return_value.query.call_count == 1

@pytest.mark.asyncio
async def test_cache_expiration(service_resolver):
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        endpoint = ServiceEndpoint(
            id="test-endpoint",
            service="test-service",
            host="localhost",
            port=8080,
            ttl=0.1  # 100ms TTL
        )
        mock_registry.return_value.query.return_value = [endpoint]
        
        # First resolution
        await service_resolver.resolve("test-service")
        
        # Wait for cache expiration
        await asyncio.sleep(0.2)
        
        # Second resolution (should query registry again)
        await service_resolver.resolve("test-service")
        assert mock_registry.return_value.query.call_count == 2

@pytest.mark.asyncio
async def test_load_balancing(service_resolver, sample_endpoints):
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mock_registry.return_value.query.return_value = sample_endpoints
        
        # Resolve multiple times
        resolutions = [
            await service_resolver.resolve("test-service")
            for _ in range(6)
        ]
        
        # Check round-robin distribution
        endpoint_ids = [endpoint.id for endpoint in resolutions]
        assert len(set(endpoint_ids)) == len(sample_endpoints)
        assert endpoint_ids[:3] != endpoint_ids[3:6]  # Different order in second round

@pytest.mark.asyncio
async def test_resolution_filtering(service_resolver):
    endpoints = [
        ServiceEndpoint(
            id=f"endpoint-{i}",
            service="test-service",
            host=f"host-{i}",
            port=8080,
            metadata={"region": "us-west" if i % 2 == 0 else "us-east"}
        )
        for i in range(4)
    ]
    
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mock_registry.return_value.query.return_value = endpoints
        
        # Resolve with filter
        filtered = await service_resolver.resolve(
            "test-service",
            filter_func=lambda e: e.metadata["region"] == "us-west"
        )
        
        assert filtered.metadata["region"] == "us-west"

@pytest.mark.asyncio
async def test_resolution_retry(service_resolver):
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        # Mock registry to fail twice then succeed
        mock_registry.return_value.query.side_effect = [
            Exception("Query failed"),
            Exception("Query failed"),
            [ServiceEndpoint(
                id="test-endpoint",
                service="test-service",
                host="localhost",
                port=8080
            )]
        ]
        
        endpoint = await service_resolver.resolve("test-service")
        
        assert endpoint.id == "test-endpoint"
        assert mock_registry.return_value.query.call_count == 3

@pytest.mark.asyncio
async def test_custom_load_balancing(service_resolver, sample_endpoints):
    class WeightedStrategy(LoadBalancingStrategy):
        async def select(self, endpoints):
            # Select endpoint with highest weight
            return max(endpoints, key=lambda e: e.metadata.get("weight", 0))
    
    # Set custom strategy
    service_resolver.load_balancer = WeightedStrategy()
    
    # Add weights to endpoints
    for i, endpoint in enumerate(sample_endpoints):
        endpoint.metadata["weight"] = i
    
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mock_registry.return_value.query.return_value = sample_endpoints
        
        selected = await service_resolver.resolve("test-service")
        assert selected.metadata["weight"] == 2  # Highest weight

@pytest.mark.asyncio
async def test_resolution_events(service_resolver, sample_endpoints):
    events = []
    
    def event_handler(event_type, service, endpoint):
        events.append((event_type, service, endpoint))
    
    service_resolver.on_resolution_event(event_handler)
    
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mock_registry.return_value.query.return_value = sample_endpoints
        
        await service_resolver.resolve("test-service")
        
        assert len(events) == 1
        assert events[0][0] == "resolved"
        assert events[0][1] == "test-service"

@pytest.mark.asyncio
async def test_resolution_metrics(service_resolver, sample_endpoints):
    with patch('datapunk_shared.metrics.MetricsCollector') as mock_collector:
        with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
            mock_registry.return_value.query.return_value = sample_endpoints
            
            await service_resolver.resolve("test-service")
            
            mock_collector.return_value.record_counter.assert_called()
            mock_collector.return_value.record_histogram.assert_called()

@pytest.mark.asyncio
async def test_resolution_cache_management(service_resolver, sample_endpoints):
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mock_registry.return_value.query.return_value = sample_endpoints
        
        # Fill cache
        await service_resolver.resolve("test-service")
        assert len(service_resolver.cache) > 0
        
        # Clear cache
        await service_resolver.clear_cache()
        assert len(service_resolver.cache) == 0

@pytest.mark.asyncio
async def test_concurrent_resolution(service_resolver, sample_endpoints):
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mock_registry.return_value.query.return_value = sample_endpoints
        
        # Perform concurrent resolutions
        tasks = [
            service_resolver.resolve("test-service")
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(isinstance(r, ServiceEndpoint) for r in results)

@pytest.mark.asyncio
async def test_resolution_error_handling(service_resolver):
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        # Mock registry to always fail
        mock_registry.return_value.query.side_effect = Exception("Query failed")
        
        with pytest.raises(ResolutionError):
            await service_resolver.resolve("test-service")

@pytest.mark.asyncio
async def test_health_aware_resolution(service_resolver, sample_endpoints):
    # Add health status to endpoints
    for i, endpoint in enumerate(sample_endpoints):
        endpoint.metadata["health_status"] = "healthy" if i < 2 else "unhealthy"
    
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mock_registry.return_value.query.return_value = sample_endpoints
        
        # Resolve with health check
        endpoint = await service_resolver.resolve(
            "test-service",
            filter_func=lambda e: e.metadata["health_status"] == "healthy"
        )
        
        assert endpoint.metadata["health_status"] == "healthy"

@pytest.mark.asyncio
async def test_cleanup(service_resolver, sample_endpoints):
    cleanup_called = False
    
    async def cleanup_handler():
        nonlocal cleanup_called
        cleanup_called = True
    
    service_resolver.on_cleanup(cleanup_handler)
    
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mock_registry.return_value.query.return_value = sample_endpoints
        await service_resolver.resolve("test-service")
    
    await service_resolver.cleanup()
    
    assert cleanup_called
    assert len(service_resolver.cache) == 0