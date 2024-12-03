import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import dns.resolver
import dns.asyncresolver
from datapunk_shared.mesh.discovery.dns_resolver import (
    DNSResolverConfig,
    DNSServiceResolver,
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
def dns_config():
    return DNSResolverConfig(
        dns_servers=["10.0.0.1"],
        dns_port=53,
        timeout=1.0,
        cache_ttl=30,
        max_retries=2,
        failover_delay=0.1
    )

@pytest.fixture
def dns_resolver(dns_config, mock_cache):
    return DNSServiceResolver(dns_config, mock_cache)

class MockSRVAnswer:
    def __init__(self, target, port):
        self.target = Mock()
        self.target.to_text.return_value = target
        self.port = port

class MockDNSAnswer:
    def __init__(self, addresses):
        self._addresses = addresses
        
    def __iter__(self):
        return iter(self._addresses)

@pytest.mark.asyncio
async def test_resolve_service_basic(dns_resolver):
    """Test basic service resolution"""
    # Mock DNS responses
    with patch.object(dns.asyncresolver.Resolver, 'resolve') as mock_resolve:
        # Mock SRV record response
        mock_resolve.return_value = [
            MockSRVAnswer("service1.example.com", 8080)
        ]
        
        # Mock A record response
        mock_resolve.side_effect = [
            [MockSRVAnswer("service1.example.com", 8080)],
            MockDNSAnswer(["192.168.1.10"])
        ]
        
        # Resolve service
        instances = await dns_resolver.resolve_service("example-service")
        
        assert len(instances) == 1
        assert instances[0].host == "192.168.1.10"
        assert instances[0].port == 8080
        assert instances[0].service_name == "example-service"

@pytest.mark.asyncio
async def test_resolve_service_with_cache(dns_resolver, mock_cache):
    """Test service resolution with caching"""
    # Prepare cached data
    cached_instance = ServiceRegistration(
        id="cached-1",
        service_name="cached-service",
        host="192.168.1.100",
        port=8080,
        metadata=ServiceMetadata(
            version="1.0",
            environment="prod",
            region="us-west"
        )
    )
    
    mock_cache.get.return_value = [cached_instance]
    
    # Resolve service (should use cache)
    instances = await dns_resolver.resolve_service("cached-service")
    
    assert len(instances) == 1
    assert instances[0].id == "cached-1"
    assert instances[0].host == "192.168.1.100"
    
    # Verify cache was checked
    mock_cache.get.assert_called_once_with("dns:cached-service")

@pytest.mark.asyncio
async def test_resolve_service_with_metadata_filter(dns_resolver):
    """Test service resolution with metadata filtering"""
    # Mock DNS responses
    with patch.object(dns.asyncresolver.Resolver, 'resolve') as mock_resolve:
        # Mock SRV records
        mock_resolve.return_value = [
            MockSRVAnswer("service1.example.com", 8080),
            MockSRVAnswer("service2.example.com", 8080)
        ]
        
        # Mock A records
        mock_resolve.side_effect = [
            [MockSRVAnswer("service1.example.com", 8080),
             MockSRVAnswer("service2.example.com", 8080)],
            MockDNSAnswer(["192.168.1.10"]),
            MockDNSAnswer(["192.168.1.11"])
        ]
        
        # Resolve with metadata filter
        instances = await dns_resolver.resolve_service(
            "example-service",
            metadata_filter={"environment": "prod"}
        )
        
        # All instances should have metadata matching the filter
        for instance in instances:
            assert instance.metadata.tags.get("environment") == "prod"

@pytest.mark.asyncio
async def test_resolve_service_failover(dns_resolver):
    """Test service resolution with failover"""
    with patch.object(dns.asyncresolver.Resolver, 'resolve') as mock_resolve:
        # First attempt fails
        mock_resolve.side_effect = dns.resolver.NoAnswer()
        
        # Second attempt succeeds
        mock_resolve.side_effect = [
            dns.resolver.NoAnswer(),
            [MockSRVAnswer("service1.example.com", 8080)],
            MockDNSAnswer(["192.168.1.10"])
        ]
        
        # Resolve service (should retry and succeed)
        instances = await dns_resolver.resolve_service("example-service")
        
        assert len(instances) == 1
        assert instances[0].host == "192.168.1.10"

@pytest.mark.asyncio
async def test_resolve_service_ipv6(dns_resolver):
    """Test service resolution with IPv6 support"""
    with patch.object(dns.asyncresolver.Resolver, 'resolve') as mock_resolve:
        # Mock SRV record
        mock_resolve.return_value = [
            MockSRVAnswer("service1.example.com", 8080)
        ]
        
        # Mock A and AAAA records
        mock_resolve.side_effect = [
            [MockSRVAnswer("service1.example.com", 8080)],
            MockDNSAnswer(["192.168.1.10"]),  # IPv4
            MockDNSAnswer(["2001:db8::1"])    # IPv6
        ]
        
        # Resolve service
        instances = await dns_resolver.resolve_service("example-service")
        
        # Should have both IPv4 and IPv6 addresses
        assert len(instances) == 2
        addresses = {instance.host for instance in instances}
        assert "192.168.1.10" in addresses
        assert "2001:db8::1" in addresses

@pytest.mark.asyncio
async def test_resolve_service_cache_update(dns_resolver, mock_cache):
    """Test cache updates during service resolution"""
    with patch.object(dns.asyncresolver.Resolver, 'resolve') as mock_resolve:
        # Mock DNS responses
        mock_resolve.return_value = [
            MockSRVAnswer("service1.example.com", 8080)
        ]
        
        mock_resolve.side_effect = [
            [MockSRVAnswer("service1.example.com", 8080)],
            MockDNSAnswer(["192.168.1.10"])
        ]
        
        # Resolve service
        instances = await dns_resolver.resolve_service("example-service")
        
        # Verify cache was updated
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args[0]
        assert call_args[0] == "dns:example-service"
        assert isinstance(call_args[1], list)
        assert isinstance(call_args[2], timedelta)
        assert call_args[2].seconds == dns_resolver.config.cache_ttl

@pytest.mark.asyncio
async def test_resolve_service_no_instances(dns_resolver):
    """Test service resolution when no instances are found"""
    with patch.object(dns.asyncresolver.Resolver, 'resolve') as mock_resolve:
        # Mock empty DNS response
        mock_resolve.return_value = []
        
        # Resolve service
        instances = await dns_resolver.resolve_service("example-service")
        
        assert len(instances) == 0

@pytest.mark.asyncio
async def test_resolve_service_partial_failure(dns_resolver):
    """Test service resolution with partial DNS failures"""
    with patch.object(dns.asyncresolver.Resolver, 'resolve') as mock_resolve:
        # Mock SRV records (two services)
        mock_resolve.return_value = [
            MockSRVAnswer("service1.example.com", 8080),
            MockSRVAnswer("service2.example.com", 8080)
        ]
        
        # First A record succeeds, second fails
        mock_resolve.side_effect = [
            [MockSRVAnswer("service1.example.com", 8080),
             MockSRVAnswer("service2.example.com", 8080)],
            MockDNSAnswer(["192.168.1.10"]),
            dns.resolver.NoAnswer()
        ]
        
        # Resolve service
        instances = await dns_resolver.resolve_service("example-service")
        
        # Should have one successful resolution
        assert len(instances) == 1
        assert instances[0].host == "192.168.1.10" 