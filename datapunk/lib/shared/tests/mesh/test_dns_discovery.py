import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh import (
    DNSDiscovery,
    DNSConfig,
    ServiceRecord,
    DNSError,
    ServiceEndpoint
)

@pytest.fixture
def dns_config():
    return DNSConfig(
        domain="service.local",
        ttl=300,  # 5 minutes
        refresh_interval=60,  # 1 minute
        max_retries=3,
        retry_delay=0.1
    )

@pytest.fixture
def dns_discovery(dns_config):
    return DNSDiscovery(config=dns_config)

@pytest.fixture
def sample_records():
    return [
        ServiceRecord(
            name="service-1",
            host="host1.service.local",
            port=8080,
            priority=10,
            weight=100
        ),
        ServiceRecord(
            name="service-2",
            host="host2.service.local",
            port=8081,
            priority=20,
            weight=50
        )
    ]

@pytest.mark.asyncio
async def test_discovery_initialization(dns_discovery, dns_config):
    assert dns_discovery.config == dns_config
    assert dns_discovery.domain == "service.local"
    assert len(dns_discovery.cache) == 0
    assert not dns_discovery.is_closed

@pytest.mark.asyncio
async def test_service_resolution():
    with patch('aiodns.DNSResolver') as mock_resolver:
        discovery = DNSDiscovery(DNSConfig(
            domain="service.local"
        ))
        
        # Mock DNS response
        mock_response = Mock()
        mock_response.host = "host1.service.local"
        mock_response.port = 8080
        mock_resolver.return_value.query.return_value = [mock_response]
        
        result = await discovery.resolve_service("test-service")
        
        assert result.host == "host1.service.local"
        assert result.port == 8080

@pytest.mark.asyncio
async def test_cache_management(dns_discovery, sample_records):
    # Add records to cache
    for record in sample_records:
        dns_discovery.cache.add(record)
    
    # Check cache contents
    cached_records = dns_discovery.cache.get_all()
    assert len(cached_records) == 2
    assert all(isinstance(r, ServiceRecord) for r in cached_records)

@pytest.mark.asyncio
async def test_ttl_expiration(dns_discovery):
    # Create record with short TTL
    record = ServiceRecord(
        name="test-service",
        host="test.service.local",
        port=8080,
        ttl=0.1  # 100ms TTL
    )
    
    dns_discovery.cache.add(record)
    assert len(dns_discovery.cache.get_all()) == 1
    
    # Wait for expiration
    await asyncio.sleep(0.2)
    assert len(dns_discovery.cache.get_all()) == 0

@pytest.mark.asyncio
async def test_refresh_mechanism():
    with patch('aiodns.DNSResolver') as mock_resolver:
        discovery = DNSDiscovery(DNSConfig(
            domain="service.local",
            refresh_interval=0.1
        ))
        
        refresh_count = 0
        
        async def mock_refresh():
            nonlocal refresh_count
            refresh_count += 1
            return True
        
        discovery._refresh_cache = mock_refresh
        
        # Start refresh task
        refresh_task = asyncio.create_task(discovery._refresh_loop())
        await asyncio.sleep(0.3)
        refresh_task.cancel()
        
        assert refresh_count >= 2

@pytest.mark.asyncio
async def test_error_handling(dns_discovery):
    with patch('aiodns.DNSResolver') as mock_resolver:
        mock_resolver.return_value.query.side_effect = Exception("DNS query failed")
        
        with pytest.raises(DNSError):
            await dns_discovery.resolve_service("test-service")

@pytest.mark.asyncio
async def test_service_registration(dns_discovery):
    endpoint = ServiceEndpoint(
        host="test.service.local",
        port=8080,
        protocol="http"
    )
    
    result = await dns_discovery.register_service(
        name="test-service",
        endpoint=endpoint
    )
    
    assert result
    cached_record = dns_discovery.cache.get("test-service")
    assert cached_record.host == endpoint.host
    assert cached_record.port == endpoint.port

@pytest.mark.asyncio
async def test_service_deregistration(dns_discovery, sample_records):
    # Add records to cache
    for record in sample_records:
        dns_discovery.cache.add(record)
    
    # Deregister service
    await dns_discovery.deregister_service("service-1")
    
    cached_records = dns_discovery.cache.get_all()
    assert len(cached_records) == 1
    assert cached_records[0].name == "service-2"

@pytest.mark.asyncio
async def test_concurrent_resolution(dns_discovery):
    with patch('aiodns.DNSResolver') as mock_resolver:
        # Mock DNS response
        mock_response = Mock()
        mock_response.host = "host1.service.local"
        mock_response.port = 8080
        mock_resolver.return_value.query.return_value = [mock_response]
        
        # Perform concurrent resolutions
        services = ["service-1", "service-2", "service-3"]
        results = await asyncio.gather(*[
            dns_discovery.resolve_service(service)
            for service in services
        ])
        
        assert len(results) == 3
        assert all(r.host == "host1.service.local" for r in results)

@pytest.mark.asyncio
async def test_metrics_collection(dns_discovery):
    with patch('datapunk_shared.metrics.MetricsCollector') as mock_collector:
        # Perform some operations
        endpoint = ServiceEndpoint(
            host="test.service.local",
            port=8080,
            protocol="http"
        )
        
        await dns_discovery.register_service(
            name="test-service",
            endpoint=endpoint
        )
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_gauge.assert_called()

@pytest.mark.asyncio
async def test_cache_persistence(dns_discovery, sample_records):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        # Add records to cache
        for record in sample_records:
            dns_discovery.cache.add(record)
        
        await dns_discovery.save_cache()
        mock_file.write.assert_called_once()
        
        await dns_discovery.load_cache()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_service_health_check(dns_discovery):
    health_checks = []
    
    async def mock_health_check(endpoint):
        health_checks.append(endpoint)
        return True
    
    dns_discovery.health_checker = mock_health_check
    
    endpoint = ServiceEndpoint(
        host="test.service.local",
        port=8080,
        protocol="http"
    )
    
    await dns_discovery.register_service(
        name="test-service",
        endpoint=endpoint,
        health_check=True
    )
    
    assert len(health_checks) == 1
    assert health_checks[0].host == endpoint.host

@pytest.mark.asyncio
async def test_service_filtering(dns_discovery, sample_records):
    # Add records to cache
    for record in sample_records:
        dns_discovery.cache.add(record)
    
    # Filter services by port
    filtered_records = dns_discovery.filter_services(
        lambda r: r.port > 8080
    )
    
    assert len(filtered_records) == 1
    assert filtered_records[0].name == "service-2"

@pytest.mark.asyncio
async def test_load_balancing(dns_discovery):
    # Add multiple records for same service
    records = [
        ServiceRecord(
            name="test-service",
            host=f"host{i}.service.local",
            port=8080,
            weight=100-i*10
        )
        for i in range(3)
    ]
    
    for record in records:
        dns_discovery.cache.add(record)
    
    # Resolve service multiple times
    resolutions = [
        await dns_discovery.resolve_service("test-service")
        for _ in range(5)
    ]
    
    # Check load balancing distribution
    hosts = [r.host for r in resolutions]
    assert len(set(hosts)) > 1  # Should use different hosts

@pytest.mark.asyncio
async def test_cleanup(dns_discovery, sample_records):
    cleanup_called = False
    
    async def cleanup_handler():
        nonlocal cleanup_called
        cleanup_called = True
    
    dns_discovery.on_cleanup(cleanup_handler)
    
    # Add records and perform cleanup
    for record in sample_records:
        dns_discovery.cache.add(record)
    
    await dns_discovery.cleanup()
    
    assert cleanup_called
    assert len(dns_discovery.cache.get_all()) == 0 