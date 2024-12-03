"""Tests for service discovery integration"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
import asyncio
from datapunk_shared.mesh.circuit_breaker.discovery_integration import (
    ServiceDiscoveryIntegration,
    DiscoveryConfig,
    ServiceInstance,
    InstanceState
)

@pytest.fixture
def metrics_client():
    return AsyncMock()

@pytest.fixture
def discovery_config():
    return DiscoveryConfig(
        refresh_interval_ms=100.0,
        instance_timeout_ms=500.0,
        connection_limit=5,
        drain_timeout_ms=200.0
    )

@pytest.fixture
def discovery_integration(metrics_client, discovery_config):
    integration = ServiceDiscoveryIntegration(
        config=discovery_config,
        metrics_client=metrics_client
    )
    return integration

@pytest.fixture
def test_instance():
    return ServiceInstance(
        instance_id="test-1",
        host="localhost",
        port=8080,
        metadata={"version": "1.0"},
        state=InstanceState.ACTIVE,
        last_seen=datetime.utcnow(),
        health_score=1.0,
        connection_count=0
    )

class TestServiceDiscoveryIntegration:
    @pytest.mark.asyncio
    async def test_instance_registration(self, discovery_integration, test_instance):
        await discovery_integration.register_instance("test-service", test_instance)
        
        assert "test-service" in discovery_integration.instances
        assert test_instance.instance_id in discovery_integration.instances["test-service"]
        assert discovery_integration.instances["test-service"][test_instance.instance_id] == test_instance

    @pytest.mark.asyncio
    async def test_instance_deregistration(self, discovery_integration, test_instance):
        await discovery_integration.register_instance("test-service", test_instance)
        await discovery_integration.deregister_instance("test-service", test_instance.instance_id)
        
        assert ("test-service", test_instance.instance_id) in discovery_integration.draining_instances
        assert discovery_integration.instances["test-service"][test_instance.instance_id].state == InstanceState.DRAINING

    @pytest.mark.asyncio
    async def test_get_instance(self, discovery_integration, test_instance):
        await discovery_integration.register_instance("test-service", test_instance)
        
        # Basic instance retrieval
        instance = await discovery_integration.get_instance("test-service")
        assert instance == test_instance
        
        # With metadata requirements
        instance = await discovery_integration.get_instance(
            "test-service",
            metadata_requirements={"version": "1.0"}
        )
        assert instance == test_instance
        
        # With non-matching metadata
        instance = await discovery_integration.get_instance(
            "test-service",
            metadata_requirements={"version": "2.0"}
        )
        assert instance is None

    @pytest.mark.asyncio
    async def test_connection_pooling(self, discovery_integration, test_instance):
        await discovery_integration.register_instance("test-service", test_instance)
        
        # Get connection
        conn1 = await discovery_integration.get_connection(
            "test-service",
            test_instance.instance_id
        )
        
        # Release connection
        await discovery_integration.release_connection(
            "test-service",
            test_instance.instance_id,
            conn1
        )
        
        # Get same connection from pool
        conn2 = await discovery_integration.get_connection(
            "test-service",
            test_instance.instance_id
        )
        
        assert conn1 == conn2

    @pytest.mark.asyncio
    async def test_instance_health_updates(self, discovery_integration, test_instance):
        await discovery_integration.register_instance("test-service", test_instance)
        
        # Update health score
        await discovery_integration.update_instance_health(
            "test-service",
            test_instance.instance_id,
            0.5
        )
        
        instance = discovery_integration.instances["test-service"][test_instance.instance_id]
        assert instance.health_score == 0.5

    @pytest.mark.asyncio
    async def test_instance_timeout(self, discovery_integration, test_instance):
        await discovery_integration.register_instance("test-service", test_instance)
        
        # Set last seen to trigger timeout
        instance = discovery_integration.instances["test-service"][test_instance.instance_id]
        instance.last_seen = datetime.utcnow() - timedelta(seconds=1)
        
        # Run timeout check
        await discovery_integration._check_instance_timeouts()
        
        assert instance.state == InstanceState.FAILED
        assert ("test-service", test_instance.instance_id) in discovery_integration.draining_instances

    @pytest.mark.asyncio
    async def test_connection_limit(self, discovery_integration, test_instance):
        await discovery_integration.register_instance("test-service", test_instance)
        
        # Create maximum connections
        for _ in range(discovery_integration.config.connection_limit):
            await discovery_integration.get_connection(
                "test-service",
                test_instance.instance_id
            )
            
        # Try to get one more connection
        instance = await discovery_integration.get_instance("test-service")
        assert instance is None

    @pytest.mark.asyncio
    async def test_background_tasks(self, discovery_integration):
        await discovery_integration.start()
        assert discovery_integration._running
        assert discovery_integration.refresh_task is not None
        assert discovery_integration.drain_task is not None
        
        await discovery_integration.stop()
        assert not discovery_integration._running
        assert discovery_integration.refresh_task.cancelled()
        assert discovery_integration.drain_task.cancelled()

    @pytest.mark.asyncio
    async def test_metrics_recording(self, discovery_integration, test_instance, metrics_client):
        await discovery_integration.register_instance("test-service", test_instance)
        
        assert metrics_client.increment.called
        metrics_client.increment.assert_any_call(
            "discovery_instance_registered",
            {
                "service_id": "test-service",
                "instance_id": test_instance.instance_id
            }
        )

    @pytest.mark.asyncio
    async def test_drain_inactive_instances(self, discovery_integration, test_instance):
        await discovery_integration.register_instance("test-service", test_instance)
        await discovery_integration.deregister_instance("test-service", test_instance.instance_id)
        
        # Run drain process
        await discovery_integration._drain_inactive_instances()
        
        assert test_instance.instance_id not in discovery_integration.instances.get("test-service", {})
        assert ("test-service", test_instance.instance_id) not in discovery_integration.draining_instances

    @pytest.mark.asyncio
    async def test_multiple_instances(self, discovery_integration):
        # Register multiple instances
        instances = []
        for i in range(3):
            instance = ServiceInstance(
                instance_id=f"test-{i}",
                host="localhost",
                port=8080 + i,
                metadata={"version": "1.0"},
                state=InstanceState.ACTIVE,
                last_seen=datetime.utcnow(),
                health_score=1.0 - (i * 0.2),  # Decreasing health scores
                connection_count=i  # Increasing connection counts
            )
            instances.append(instance)
            await discovery_integration.register_instance("test-service", instance)
            
        # Get best instance (should be first one due to health score and connection count)
        best_instance = await discovery_integration.get_instance("test-service")
        assert best_instance.instance_id == "test-0"

    @pytest.mark.asyncio
    async def test_error_handling(self, discovery_integration, test_instance):
        # Test non-existent service
        instance = await discovery_integration.get_instance("non-existent")
        assert instance is None
        
        # Test non-existent instance
        conn = await discovery_integration.get_connection("test-service", "non-existent")
        assert conn is None
        
        # Test invalid connection release
        await discovery_integration.release_connection(
            "non-existent",
            "non-existent",
            None
        )  # Should not raise exception 