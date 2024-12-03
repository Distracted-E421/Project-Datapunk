import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.routing import (
    LoadBalancer,
    BalancerConfig,
    RoutingStrategy,
    ServiceEndpoint,
    BalancerError
)

@pytest.fixture
def balancer_config():
    return BalancerConfig(
        strategy=RoutingStrategy.ROUND_ROBIN,
        health_check_interval=5,
        retry_attempts=3,
        circuit_breaker_enabled=True
    )

@pytest.fixture
def load_balancer(balancer_config):
    return LoadBalancer(config=balancer_config)

@pytest.fixture
def sample_endpoints():
    return [
        ServiceEndpoint(
            id="service1",
            host="host1",
            port=8080,
            weight=1,
            health_check_url="/health"
        ),
        ServiceEndpoint(
            id="service2",
            host="host2",
            port=8080,
            weight=2,
            health_check_url="/health"
        ),
        ServiceEndpoint(
            id="service3",
            host="host3",
            port=8080,
            weight=1,
            health_check_url="/health"
        )
    ]

@pytest.mark.asyncio
async def test_balancer_initialization(load_balancer, balancer_config):
    assert load_balancer.config == balancer_config
    assert load_balancer.strategy == RoutingStrategy.ROUND_ROBIN
    assert len(load_balancer.endpoints) == 0

@pytest.mark.asyncio
async def test_endpoint_registration(load_balancer, sample_endpoints):
    for endpoint in sample_endpoints:
        await load_balancer.register_endpoint(endpoint)
    
    assert len(load_balancer.endpoints) == len(sample_endpoints)
    assert all(e.id in load_balancer.endpoints for e in sample_endpoints)

@pytest.mark.asyncio
async def test_round_robin_routing(load_balancer, sample_endpoints):
    for endpoint in sample_endpoints:
        await load_balancer.register_endpoint(endpoint)
    
    # Test round-robin distribution
    selected = [
        await load_balancer.select_endpoint()
        for _ in range(len(sample_endpoints))
    ]
    
    # Each endpoint should be selected once
    assert len(set(e.id for e in selected)) == len(sample_endpoints)

@pytest.mark.asyncio
async def test_weighted_routing(load_balancer, sample_endpoints):
    load_balancer.strategy = RoutingStrategy.WEIGHTED
    
    for endpoint in sample_endpoints:
        await load_balancer.register_endpoint(endpoint)
    
    # Test weighted distribution
    selections = {}
    for _ in range(100):
        endpoint = await load_balancer.select_endpoint()
        selections[endpoint.id] = selections.get(endpoint.id, 0) + 1
    
    # Endpoint with weight=2 should be selected more often
    assert selections["service2"] > selections["service1"]
    assert selections["service2"] > selections["service3"]

@pytest.mark.asyncio
async def test_health_checks(load_balancer, sample_endpoints):
    with patch.object(load_balancer, '_check_endpoint_health') as mock_check:
        mock_check.side_effect = [True, False, True]
        
        for endpoint in sample_endpoints:
            await load_balancer.register_endpoint(endpoint)
        
        await load_balancer.check_health()
        
        # Unhealthy endpoint should be removed from rotation
        assert len(load_balancer.healthy_endpoints) == 2

@pytest.mark.asyncio
async def test_circuit_breaker_integration(load_balancer, sample_endpoints):
    endpoint = sample_endpoints[0]
    await load_balancer.register_endpoint(endpoint)
    
    # Simulate failures
    for _ in range(load_balancer.config.failure_threshold):
        await load_balancer.record_failure(endpoint.id)
    
    # Circuit should be open
    assert not await load_balancer.is_endpoint_available(endpoint.id)

@pytest.mark.asyncio
async def test_retry_mechanism(load_balancer, sample_endpoints):
    with patch.object(load_balancer, '_try_endpoint') as mock_try:
        mock_try.side_effect = [
            Exception("Connection failed"),
            Exception("Connection failed"),
            True
        ]
        
        await load_balancer.register_endpoint(sample_endpoints[0])
        result = await load_balancer.try_endpoint_with_retry(sample_endpoints[0])
        
        assert result is True
        assert mock_try.call_count == 3

@pytest.mark.asyncio
async def test_endpoint_metrics(load_balancer, sample_endpoints):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        endpoint = sample_endpoints[0]
        await load_balancer.register_endpoint(endpoint)
        
        # Record some metrics
        await load_balancer.record_latency(endpoint.id, 0.1)
        await load_balancer.record_success(endpoint.id)
        
        mock_collector.return_value.record_histogram.assert_called()
        mock_collector.return_value.record_counter.assert_called()

@pytest.mark.asyncio
async def test_endpoint_removal(load_balancer, sample_endpoints):
    for endpoint in sample_endpoints:
        await load_balancer.register_endpoint(endpoint)
    
    await load_balancer.remove_endpoint(sample_endpoints[0].id)
    
    assert len(load_balancer.endpoints) == len(sample_endpoints) - 1
    assert sample_endpoints[0].id not in load_balancer.endpoints

@pytest.mark.asyncio
async def test_least_connections_routing(load_balancer, sample_endpoints):
    load_balancer.strategy = RoutingStrategy.LEAST_CONNECTIONS
    
    for endpoint in sample_endpoints:
        await load_balancer.register_endpoint(endpoint)
    
    # Simulate active connections
    await load_balancer.record_connection_start(sample_endpoints[0].id)
    await load_balancer.record_connection_start(sample_endpoints[0].id)
    
    # Should select endpoint with least connections
    selected = await load_balancer.select_endpoint()
    assert selected.id != sample_endpoints[0].id

@pytest.mark.asyncio
async def test_endpoint_recovery(load_balancer, sample_endpoints):
    endpoint = sample_endpoints[0]
    await load_balancer.register_endpoint(endpoint)
    
    # Mark endpoint as unhealthy
    await load_balancer.mark_endpoint_unhealthy(endpoint.id)
    assert endpoint.id not in load_balancer.healthy_endpoints
    
    # Recover endpoint
    await load_balancer.mark_endpoint_healthy(endpoint.id)
    assert endpoint.id in load_balancer.healthy_endpoints

@pytest.mark.asyncio
async def test_sticky_routing(load_balancer, sample_endpoints):
    load_balancer.strategy = RoutingStrategy.STICKY
    
    for endpoint in sample_endpoints:
        await load_balancer.register_endpoint(endpoint)
    
    # Same key should route to same endpoint
    key = "user123"
    endpoint1 = await load_balancer.select_endpoint(sticky_key=key)
    endpoint2 = await load_balancer.select_endpoint(sticky_key=key)
    
    assert endpoint1.id == endpoint2.id

@pytest.mark.asyncio
async def test_concurrent_routing(load_balancer, sample_endpoints):
    for endpoint in sample_endpoints:
        await load_balancer.register_endpoint(endpoint)
    
    # Test concurrent endpoint selection
    results = await asyncio.gather(*[
        load_balancer.select_endpoint()
        for _ in range(10)
    ])
    
    assert len(results) == 10
    assert all(r is not None for r in results)

@pytest.mark.asyncio
async def test_balancer_events(load_balancer, sample_endpoints):
    events = []
    
    def event_handler(event_type, endpoint_id):
        events.append((event_type, endpoint_id))
    
    load_balancer.on_balancer_event(event_handler)
    
    endpoint = sample_endpoints[0]
    await load_balancer.register_endpoint(endpoint)
    await load_balancer.remove_endpoint(endpoint.id)
    
    assert len(events) == 2
    assert events[0][0] == "endpoint_added"
    assert events[1][0] == "endpoint_removed"

@pytest.mark.asyncio
async def test_error_handling(load_balancer):
    with pytest.raises(BalancerError):
        await load_balancer.select_endpoint()  # No endpoints registered

@pytest.mark.asyncio
async def test_load_distribution(load_balancer, sample_endpoints):
    load_balancer.strategy = RoutingStrategy.LEAST_LOADED
    
    for endpoint in sample_endpoints:
        await load_balancer.register_endpoint(endpoint)
    
    # Simulate load on endpoints
    await load_balancer.record_load(sample_endpoints[0].id, 0.8)  # 80% load
    await load_balancer.record_load(sample_endpoints[1].id, 0.3)  # 30% load
    await load_balancer.record_load(sample_endpoints[2].id, 0.5)  # 50% load
    
    # Should select least loaded endpoint
    selected = await load_balancer.select_endpoint()
    assert selected.id == sample_endpoints[1].id 