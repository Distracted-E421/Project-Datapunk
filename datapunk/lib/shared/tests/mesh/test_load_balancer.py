import pytest
from datapunk.lib.shared.datapunk_shared.mesh.load_balancer.load_balancer import LoadBalancer, LoadBalancerStrategy, ServiceInstance
from datapunk_shared.mesh.metrics import LoadBalancerMetrics

@pytest.fixture
def load_balancer():
    return LoadBalancer(strategy=LoadBalancerStrategy.ROUND_ROBIN)

@pytest.fixture
def service_instances():
    return [
        ServiceInstance(id="test1", address="localhost", port=8001, weight=1),
        ServiceInstance(id="test2", address="localhost", port=8002, weight=2),
        ServiceInstance(id="test3", address="localhost", port=8003, weight=1)
    ]

class TestLoadBalancer:
    def test_round_robin_strategy(self, load_balancer, service_instances):
        """Test round-robin load balancing strategy."""
        service_name = "test_service"
        
        # Register instances
        for instance in service_instances:
            load_balancer.register_instance(service_name, instance)
        
        # Test round-robin selection
        selected = []
        for _ in range(len(service_instances) * 2):
            instance = load_balancer.get_next_instance(service_name)
            selected.append(instance.id)
        
        # Verify round-robin pattern
        expected_pattern = ["test1", "test2", "test3"] * 2
        assert selected == expected_pattern

    def test_least_connections_strategy(self):
        """Test least connections load balancing strategy."""
        lb = LoadBalancer(strategy=LoadBalancerStrategy.LEAST_CONNECTIONS)
        service_name = "test_service"
        
        # Create instances with different connection counts
        instances = [
            ServiceInstance(id="busy", address="localhost", port=8001, active_connections=5),
            ServiceInstance(id="moderate", address="localhost", port=8002, active_connections=2),
            ServiceInstance(id="idle", address="localhost", port=8003, active_connections=0)
        ]
        
        for instance in instances:
            lb.register_instance(service_name, instance)
        
        # Should select the instance with fewest connections
        selected = lb.get_next_instance(service_name)
        assert selected.id == "idle"

    def test_weighted_round_robin_strategy(self):
        """Test weighted round-robin load balancing strategy."""
        lb = LoadBalancer(strategy=LoadBalancerStrategy.WEIGHTED_ROUND_ROBIN)
        service_name = "test_service"
        
        # Create instances with different weights
        instances = [
            ServiceInstance(id="heavy", address="localhost", port=8001, weight=3),
            ServiceInstance(id="light", address="localhost", port=8002, weight=1)
        ]
        
        for instance in instances:
            lb.register_instance(service_name, instance)
        
        # Test selection pattern
        selected = []
        for _ in range(4):
            instance = lb.get_next_instance(service_name)
            selected.append(instance.id)
        
        # Verify weight-based distribution
        assert selected.count("heavy") == 3
        assert selected.count("light") == 1

    def test_connection_tracking(self, load_balancer):
        """Test connection tracking functionality."""
        service_name = "test_service"
        instance = ServiceInstance(id="test1", address="localhost", port=8001)
        load_balancer.register_instance(service_name, instance)
        
        # Record request start
        load_balancer.record_request_start(instance)
        assert instance.active_connections == 1
        
        # Record request completion
        load_balancer.record_request_complete(instance)
        assert instance.active_connections == 0

    def test_health_score_updates(self, load_balancer):
        """Test health score updates."""
        service_name = "test_service"
        instance = ServiceInstance(id="test1", address="localhost", port=8001)
        load_balancer.register_instance(service_name, instance)
        
        # Update health score
        load_balancer.update_health_score(instance, 0.5)
        assert instance.health_score == 0.5
        
        # Ensure health score is capped
        load_balancer.update_health_score(instance, 1.5)
        assert instance.health_score == 1.0

    @pytest.mark.asyncio
    async def test_error_handling(self, load_balancer):
        """Test error handling in load balancer."""
        service_name = "nonexistent_service"
        
        # Should handle missing service gracefully
        instance = load_balancer.get_next_instance(service_name)
        assert instance is None

    def test_instance_deregistration(self, load_balancer, service_instances):
        """Test instance deregistration."""
        service_name = "test_service"
        
        # Register instances
        for instance in service_instances:
            load_balancer.register_instance(service_name, instance)
        
        # Deregister one instance
        load_balancer.deregister_instance(service_name, "test2")
        
        # Verify instance was removed
        remaining_instances = [inst.id for inst in load_balancer.instances[service_name]]
        assert "test2" not in remaining_instances
        assert len(remaining_instances) == len(service_instances) - 1 