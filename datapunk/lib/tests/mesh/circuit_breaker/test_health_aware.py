"""Tests for health-aware circuit breaker component"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
from datapunk_shared.mesh.circuit_breaker.health_aware import (
    HealthAwareBreaker,
    HealthConfig,
    HealthStatus,
    ResourceType,
    ResourceMetrics,
    ServiceHealth
)

@pytest.fixture
def metrics_client():
    client = AsyncMock()
    # Setup default gauge values
    client.get_gauge.return_value = 0.5
    return client

@pytest.fixture
def health_config():
    return HealthConfig(
        check_interval_ms=1000.0,
        response_time_threshold_ms=500.0,
        error_rate_threshold=0.05,
        dependency_timeout_ms=200.0
    )

@pytest.fixture
def health_breaker(metrics_client, health_config):
    return HealthAwareBreaker(
        config=health_config,
        metrics_client=metrics_client
    )

class TestHealthAwareBreaker:
    @pytest.mark.asyncio
    async def test_initial_health_check(self, health_breaker):
        health = await health_breaker.check_health("test_service")
        assert health.status == HealthStatus.HEALTHY
        assert health.response_time_ms == 0.0
        assert health.error_rate == 0.0
        assert len(health.resource_metrics) == len(ResourceType)

    @pytest.mark.asyncio
    async def test_record_request_metrics(self, health_breaker):
        # Record some requests
        health_breaker.record_request("test_service", 100.0, False)
        health_breaker.record_request("test_service", 200.0, True)
        health_breaker.record_request("test_service", 150.0, False)
        
        # Check metrics
        health = await health_breaker.check_health("test_service")
        assert health.response_time_ms == 150.0  # Average
        assert health.error_rate == 1/3  # One error out of three requests

    @pytest.mark.asyncio
    async def test_resource_utilization(self, health_breaker, metrics_client):
        # Setup mock resource metrics
        metrics_client.get_gauge.side_effect = lambda metric: {
            "test_service_cpu_utilization": 0.9,
            "test_service_memory_utilization": 0.7,
            "test_service_disk_utilization": 0.5,
            "test_service_network_utilization": 0.6,
            "test_service_connections_utilization": 0.4
        }.get(metric, 0.0)
        
        health = await health_breaker.check_health("test_service")
        
        # CPU above threshold should cause degraded status
        assert health.status == HealthStatus.UNHEALTHY
        assert health.resource_metrics[ResourceType.CPU].utilization == 0.9

    @pytest.mark.asyncio
    async def test_dependency_health(self, health_breaker):
        # Add critical dependency
        health_breaker.add_critical_dependency("main_service", "dep_service")
        
        # Make dependency unhealthy
        dep_health = await health_breaker.check_health("dep_service")
        health_breaker.record_request("dep_service", 1000.0, True)  # High latency and error
        
        # Check main service health
        health = await health_breaker.check_health("main_service")
        assert health.dependencies["dep_service"] == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_request_allowance(self, health_breaker):
        # Healthy service should allow requests
        assert await health_breaker.should_allow_request("test_service")
        
        # Record degraded performance
        for _ in range(10):
            health_breaker.record_request("test_service", 600.0, False)  # High latency
            
        # Should still allow high priority requests
        assert await health_breaker.should_allow_request(
            "test_service",
            request_priority="HIGH"
        )
        
        # Should reject low priority requests
        assert not await health_breaker.should_allow_request(
            "test_service",
            request_priority="LOW"
        )

    @pytest.mark.asyncio
    async def test_resource_trend_detection(self, health_breaker, metrics_client):
        # Simulate increasing CPU utilization
        for i in range(5):
            metrics_client.get_gauge.return_value = 0.5 + (i * 0.1)
            await health_breaker.check_health("test_service")
            
        health = await health_breaker.check_health("test_service")
        cpu_metrics = health.resource_metrics[ResourceType.CPU]
        assert cpu_metrics.trend > 0  # Should detect increasing trend

    @pytest.mark.asyncio
    async def test_error_rate_thresholds(self, health_breaker):
        # Record increasing error rate
        for _ in range(10):
            health_breaker.record_request("test_service", 100.0, True)
            
        health = await health_breaker.check_health("test_service")
        assert health.status == HealthStatus.UNHEALTHY
        assert health.error_rate == 1.0

    @pytest.mark.asyncio
    async def test_metrics_recording(self, health_breaker, metrics_client):
        await health_breaker.check_health("test_service")
        
        # Verify metrics were recorded
        assert metrics_client.gauge.called
        assert metrics_client.increment.called
        
        # Verify specific metrics
        metrics_client.gauge.assert_any_call(
            "test_service_response_time",
            0.0
        )
        metrics_client.increment.assert_any_call(
            "test_service_health_status",
            {"status": "healthy"}
        )

    @pytest.mark.asyncio
    async def test_dependency_timeout(self, health_breaker, metrics_client):
        # Add dependency that will timeout
        health_breaker.add_critical_dependency("main_service", "slow_dep")
        metrics_client.get_gauge.side_effect = asyncio.TimeoutError
        
        health = await health_breaker.check_health("main_service")
        assert health.dependencies["slow_dep"] == HealthStatus.UNKNOWN

    @pytest.mark.asyncio
    async def test_resource_history_cleanup(self, health_breaker):
        # Add old resource metrics
        service_id = "test_service"
        old_time = datetime.utcnow() - timedelta(minutes=10)
        
        health_breaker.resource_history[service_id] = {
            ResourceType.CPU: [
                ResourceMetrics(0.5, 0.8, 0.0, old_time)
            ]
        }
        
        # Check health to trigger cleanup
        await health_breaker.check_health(service_id)
        
        # Old metrics should be cleaned up
        assert len(health_breaker.resource_history[service_id][ResourceType.CPU]) == 1
        assert health_breaker.resource_history[service_id][ResourceType.CPU][0].last_updated > old_time

    @pytest.mark.asyncio
    async def test_degraded_state_handling(self, health_breaker):
        # Create degraded state
        health_breaker.record_request("test_service", 600.0, False)  # Above threshold
        health = await health_breaker.check_health("test_service")
        
        assert health.status == HealthStatus.DEGRADED
        
        # Test request handling in degraded state
        assert await health_breaker.should_allow_request("test_service", "HIGH")
        assert not await health_breaker.should_allow_request("test_service", "LOW")

    @pytest.mark.asyncio
    async def test_multiple_services(self, health_breaker):
        # Test handling multiple services
        health_breaker.record_request("service1", 100.0, False)
        health_breaker.record_request("service2", 800.0, True)
        
        health1 = await health_breaker.check_health("service1")
        health2 = await health_breaker.check_health("service2")
        
        assert health1.status == HealthStatus.HEALTHY
        assert health2.status == HealthStatus.UNHEALTHY 