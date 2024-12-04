import pytest
from unittest.mock import Mock, AsyncMock
import asyncio
import time
from datapunk_shared.mesh.load_balancer.balancer import (
    LoadBalancer,
    LoadBalancerConfig,
    ServiceRegistration,
    RoundRobinStrategy
)
from datapunk_shared.monitoring import MetricsCollector

@pytest.fixture
def mock_metrics():
    metrics = Mock(spec=MetricsCollector)
    metrics.increment = AsyncMock()
    metrics.gauge = AsyncMock()
    return metrics

@pytest.fixture
def test_instances():
    return [
        ServiceRegistration(
            id=f"test-instance-{i}",
            service_name="test-service",
            host=f"192.168.1.{i}",
            port=8080
        ) for i in range(3)
    ]

@pytest.fixture
def config():
    return LoadBalancerConfig(
        strategy_type=RoundRobinStrategy,
        health_check_interval=0.1,
        health_check_timeout=0.05,
        error_threshold=2,
        recovery_threshold=1
    )

@pytest.fixture
async def load_balancer(config, mock_metrics):
    balancer = LoadBalancer(config, mock_metrics)
    await balancer.start()
    yield balancer
    await balancer.stop()

@pytest.mark.asyncio
async def test_load_balancer_instance_management(load_balancer, test_instances):
    """Test instance management functionality"""
    # Update instances
    await load_balancer.update_instances("test-service", test_instances)
    
    # Verify instances are stored
    assert "test-service" in load_balancer.instances
    assert len(load_balancer.instances["test-service"]) == len(test_instances)
    
    # Verify health states are initialized
    for instance in test_instances:
        assert instance.id in load_balancer.health_states
        assert load_balancer.health_states[instance.id].healthy
        
    # Update with fewer instances
    await load_balancer.update_instances("test-service", test_instances[:1])
    
    # Verify old instances are cleaned up
    assert len(load_balancer.instances["test-service"]) == 1
    assert len(load_balancer.health_states) == 1
    assert test_instances[0].id in load_balancer.health_states

@pytest.mark.asyncio
async def test_load_balancer_instance_selection(load_balancer, test_instances):
    """Test instance selection functionality"""
    await load_balancer.update_instances("test-service", test_instances)
    
    # Test multiple selections
    selected_ids = set()
    for _ in range(10):
        instance = await load_balancer.get_instance("test-service")
        assert instance is not None
        selected_ids.add(instance.id)
        
    # Should have used all instances
    assert len(selected_ids) == len(test_instances)
    
    # Test selection with no instances
    instance = await load_balancer.get_instance("nonexistent-service")
    assert instance is None

@pytest.mark.asyncio
async def test_load_balancer_health_tracking(load_balancer, test_instances):
    """Test health status tracking"""
    await load_balancer.update_instances("test-service", test_instances)
    instance_id = test_instances[0].id
    
    # Record failures until unhealthy
    for _ in range(load_balancer.config.error_threshold):
        await load_balancer.record_request(instance_id, 100.0, False)
        
    # Instance should be marked unhealthy
    assert not load_balancer.health_states[instance_id].healthy
    
    # Record successes until recovered
    for _ in range(load_balancer.config.recovery_threshold):
        await load_balancer.record_request(instance_id, 10.0, True)
        
    # Instance should be healthy again
    assert load_balancer.health_states[instance_id].healthy

@pytest.mark.asyncio
async def test_load_balancer_metrics(load_balancer, test_instances, mock_metrics):
    """Test metrics collection"""
    await load_balancer.update_instances("test-service", test_instances)
    instance_id = test_instances[0].id
    
    # Record successful request
    await load_balancer.record_request(instance_id, 10.0, True)
    
    # Verify metrics were recorded
    mock_metrics.gauge.assert_any_call(
        "load_balancer.instance_latency",
        10.0,
        tags={"instance_id": instance_id}
    )
    
    mock_metrics.gauge.assert_any_call(
        "load_balancer.instance_errors",
        0,
        tags={"instance_id": instance_id}
    )
    
    # Record failed request
    await load_balancer.record_request(instance_id, 20.0, False)
    
    # Verify error count metric
    mock_metrics.gauge.assert_any_call(
        "load_balancer.instance_errors",
        1,
        tags={"instance_id": instance_id}
    )

@pytest.mark.asyncio
async def test_load_balancer_health_check_timeout(load_balancer, test_instances):
    """Test health check timeout functionality"""
    await load_balancer.update_instances("test-service", test_instances)
    instance_id = test_instances[0].id
    
    # Wait for health check timeout
    await asyncio.sleep(load_balancer.config.health_check_timeout * 2)
    
    # Instance should be marked unhealthy
    assert not load_balancer.health_states[instance_id].healthy
    
    # Record activity to make healthy again
    await load_balancer.record_request(instance_id, 10.0, True)
    assert load_balancer.health_states[instance_id].healthy

@pytest.mark.asyncio
async def test_load_balancer_stats(load_balancer, test_instances):
    """Test statistics collection"""
    await load_balancer.update_instances("test-service", test_instances)
    instance_id = test_instances[0].id
    
    # Record some requests
    await load_balancer.record_request(instance_id, 10.0, True)
    await load_balancer.record_request(instance_id, 20.0, False)
    
    # Get stats
    stats = await load_balancer.get_stats()
    
    # Verify stats
    assert stats["total_requests"] == 2
    assert stats["successful_requests"] == 1
    assert stats["failed_requests"] == 1
    assert stats["avg_latency_ms"] == 15.0
    assert stats["active_instances"] == 3
    assert stats["current_strategy"] == "RoundRobinStrategy"

@pytest.mark.asyncio
async def test_load_balancer_concurrent_access(load_balancer, test_instances):
    """Test concurrent access to load balancer"""
    await load_balancer.update_instances("test-service", test_instances)
    
    # Simulate concurrent requests
    async def make_request():
        instance = await load_balancer.get_instance("test-service")
        if instance:
            await load_balancer.record_request(instance.id, 10.0, True)
        return instance
        
    # Run multiple concurrent requests
    tasks = [make_request() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    # Verify all requests got an instance
    assert all(result is not None for result in results)
    
    # Verify instance distribution
    used_instances = {result.id for result in results}
    assert len(used_instances) == len(test_instances)  # All instances were used

@pytest.mark.asyncio
async def test_load_balancer_error_handling(load_balancer, test_instances):
    """Test error handling in load balancer"""
    await load_balancer.update_instances("test-service", test_instances)
    
    # Test with invalid instance ID
    await load_balancer.record_request("invalid-id", 10.0, True)
    
    # Should not affect valid instances
    instance = await load_balancer.get_instance("test-service")
    assert instance is not None
    
    # Test with invalid service name
    instance = await load_balancer.get_instance("invalid-service")
    assert instance is None 