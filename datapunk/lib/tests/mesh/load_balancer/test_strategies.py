import pytest
from unittest.mock import Mock
import time
from datapunk_shared.mesh.load_balancer.strategies import (
    HealthStatus,
    LoadBalancerStats,
    RoundRobinStrategy,
    LeastConnectionsStrategy,
    WeightedResponseTimeStrategy,
    AdaptiveStrategy
)
from datapunk_shared.mesh.discovery.registry import ServiceRegistration

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
def healthy_states(test_instances):
    return {
        instance.id: HealthStatus(
            healthy=True,
            last_check=time.time(),
            error_count=0,
            latency_ms=10.0,
            success_rate=1.0
        )
        for instance in test_instances
    }

@pytest.mark.asyncio
async def test_round_robin_strategy(test_instances, healthy_states):
    """Test round-robin selection with health checks"""
    strategy = RoundRobinStrategy()
    
    # Test selection sequence
    selected_ids = []
    for _ in range(5):  # Select more times than instances
        instance = await strategy.select_instance(test_instances, healthy_states)
        assert instance is not None
        selected_ids.append(instance.id)
        
    # Verify round-robin pattern
    assert selected_ids[:3] == [inst.id for inst in test_instances]
    assert selected_ids[3:] == [inst.id for inst in test_instances[:2]]
    
    # Test with some unhealthy instances
    unhealthy_states = healthy_states.copy()
    unhealthy_states[test_instances[1].id].healthy = False
    
    selected = await strategy.select_instance(test_instances, unhealthy_states)
    assert selected.id != test_instances[1].id

@pytest.mark.asyncio
async def test_least_connections_strategy(test_instances, healthy_states):
    """Test least connections selection"""
    strategy = LeastConnectionsStrategy()
    
    # Add some connections
    strategy.active_connections = {
        test_instances[0].id: 2,
        test_instances[1].id: 1,
        test_instances[2].id: 3
    }
    
    # Should select instance with fewest connections
    selected = await strategy.select_instance(test_instances, healthy_states)
    assert selected.id == test_instances[1].id
    
    # Update stats and verify connection count changes
    strategy.update_stats(test_instances[1].id, 10.0, True)
    assert strategy.active_connections[test_instances[1].id] == 0

@pytest.mark.asyncio
async def test_weighted_response_time_strategy(test_instances, healthy_states):
    """Test weighted response time selection"""
    strategy = WeightedResponseTimeStrategy(smoothing_factor=0.5)
    
    # Add some response times
    strategy.response_times = {
        test_instances[0].id: 100.0,  # Slow
        test_instances[1].id: 10.0,   # Fast
        test_instances[2].id: 50.0    # Medium
    }
    
    # Count selections over many iterations
    selections = {inst.id: 0 for inst in test_instances}
    iterations = 1000
    
    for _ in range(iterations):
        selected = await strategy.select_instance(test_instances, healthy_states)
        selections[selected.id] += 1
        
    # Faster instance should be selected more often
    assert selections[test_instances[1].id] > selections[test_instances[0].id]
    assert selections[test_instances[1].id] > selections[test_instances[2].id]

@pytest.mark.asyncio
async def test_adaptive_strategy(test_instances, healthy_states):
    """Test adaptive strategy switching"""
    strategy = AdaptiveStrategy()
    
    # Initial strategy should be round-robin
    assert strategy.current_strategy == "round_robin"
    
    # Simulate poor performance with round-robin
    for _ in range(strategy.evaluation_window):
        await strategy.select_instance(test_instances, healthy_states)
        strategy.update_stats("test-instance-0", 100.0, False)
        
    # Strategy should switch after evaluation window
    await strategy.select_instance(test_instances, healthy_states)
    assert strategy.current_strategy != "round_robin"
    
    # Simulate good performance with new strategy
    for _ in range(strategy.evaluation_window):
        await strategy.select_instance(test_instances, healthy_states)
        strategy.update_stats("test-instance-0", 10.0, True)
        
    # Strategy should stick with current strategy
    current = strategy.current_strategy
    await strategy.select_instance(test_instances, healthy_states)
    assert strategy.current_strategy == current

@pytest.mark.asyncio
async def test_strategy_stats_tracking():
    """Test statistics tracking in strategies"""
    strategies = [
        RoundRobinStrategy(),
        LeastConnectionsStrategy(),
        WeightedResponseTimeStrategy(),
        AdaptiveStrategy()
    ]
    
    for strategy in strategies:
        # Initial stats should be zero
        assert strategy.stats.total_requests == 0
        assert strategy.stats.successful_requests == 0
        assert strategy.stats.failed_requests == 0
        
        # Update with success
        strategy.update_stats("test-instance", 10.0, True)
        assert strategy.stats.total_requests == 1
        assert strategy.stats.successful_requests == 1
        assert strategy.stats.failed_requests == 0
        assert strategy.stats.avg_latency_ms == 10.0
        
        # Update with failure
        strategy.update_stats("test-instance", 20.0, False)
        assert strategy.stats.total_requests == 2
        assert strategy.stats.successful_requests == 1
        assert strategy.stats.failed_requests == 1
        assert strategy.stats.avg_latency_ms == 15.0  # Average of 10 and 20

@pytest.mark.asyncio
async def test_strategy_health_awareness(test_instances):
    """Test health awareness in all strategies"""
    strategies = [
        RoundRobinStrategy(),
        LeastConnectionsStrategy(),
        WeightedResponseTimeStrategy(),
        AdaptiveStrategy()
    ]
    
    # Create health states with one unhealthy instance
    health_states = {
        instance.id: HealthStatus(
            healthy=i != 1,  # Make second instance unhealthy
            last_check=time.time()
        )
        for i, instance in enumerate(test_instances)
    }
    
    for strategy in strategies:
        # Test multiple selections
        for _ in range(10):
            selected = await strategy.select_instance(test_instances, health_states)
            assert selected is not None
            assert selected.id != test_instances[1].id  # Unhealthy instance
            assert health_states[selected.id].healthy 