"""Tests for the Dependency Chain Management System"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from datapunk_shared.mesh.circuit_breaker.dependency_chain import (
    DependencyChain,
    DependencyConfig,
    DependencyType,
    HealthStatus,
    DependencyInfo
)

@pytest.fixture
def config():
    return DependencyConfig(
        health_check_interval=0.1,
        failure_threshold=2,
        recovery_threshold=1,
        cascade_delay=0.1,
        max_retry_interval=1.0
    )

@pytest.fixture
def chain(config):
    return DependencyChain(config)

@pytest.mark.asyncio
async def test_add_dependency(chain):
    """Test adding dependencies"""
    chain.add_dependency("service1", "dep1", DependencyType.CRITICAL)
    chain.add_dependency("service1", "dep2", DependencyType.REQUIRED)
    
    assert "service1" in chain.dependencies
    assert "dep1" in chain.dependencies["service1"]
    assert "dep2" in chain.dependencies["service1"]
    assert chain.dependencies["service1"]["dep1"].dependency_type == DependencyType.CRITICAL
    assert chain.dependencies["service1"]["dep2"].dependency_type == DependencyType.REQUIRED

@pytest.mark.asyncio
async def test_remove_dependency(chain):
    """Test removing dependencies"""
    chain.add_dependency("service1", "dep1", DependencyType.CRITICAL)
    chain.add_dependency("service1", "dep2", DependencyType.REQUIRED)
    
    chain.remove_dependency("service1", "dep1")
    assert "dep1" not in chain.dependencies["service1"]
    assert "dep2" in chain.dependencies["service1"]

@pytest.mark.asyncio
async def test_health_status_update(chain):
    """Test health status updates"""
    chain.add_dependency("service1", "dep1", DependencyType.CRITICAL)
    
    await chain.update_health("dep1", HealthStatus.UNHEALTHY)
    assert chain.health_status_cache["dep1"] == HealthStatus.UNHEALTHY
    
    await chain.update_health("dep1", HealthStatus.HEALTHY)
    assert chain.health_status_cache["dep1"] == HealthStatus.HEALTHY

@pytest.mark.asyncio
async def test_cascading_failure(chain):
    """Test cascading failure handling"""
    # Setup dependency chain
    chain.add_dependency("service1", "dep1", DependencyType.CRITICAL)
    chain.add_dependency("service2", "service1", DependencyType.REQUIRED)
    
    # Fail critical dependency
    await chain.update_health("dep1", HealthStatus.UNHEALTHY)
    await asyncio.sleep(chain.config.cascade_delay * 2)
    
    # Check cascading effect
    assert chain.health_status_cache["dep1"] == HealthStatus.UNHEALTHY
    assert chain.health_status_cache["service1"] == HealthStatus.UNHEALTHY
    assert chain.health_status_cache["service2"] == HealthStatus.DEGRADED

@pytest.mark.asyncio
async def test_recovery_handling(chain):
    """Test recovery handling"""
    chain.add_dependency("service1", "dep1", DependencyType.CRITICAL)
    chain.add_dependency("service2", "service1", DependencyType.REQUIRED)
    
    # Fail and recover critical dependency
    await chain.update_health("dep1", HealthStatus.UNHEALTHY)
    await asyncio.sleep(chain.config.cascade_delay * 2)
    await chain.update_health("dep1", HealthStatus.HEALTHY)
    await asyncio.sleep(chain.config.cascade_delay * 2)
    
    # Check recovery propagation
    assert chain.health_status_cache["dep1"] == HealthStatus.HEALTHY
    assert chain.health_status_cache["service1"] == HealthStatus.HEALTHY
    assert chain.health_status_cache["service2"] == HealthStatus.HEALTHY

@pytest.mark.asyncio
async def test_health_check_loop(chain):
    """Test health check loop"""
    chain.add_dependency("service1", "dep1", DependencyType.CRITICAL)
    
    # Start monitoring
    await chain.start()
    await asyncio.sleep(chain.config.health_check_interval * 2)
    
    # Verify health checks are running
    assert "service1" in chain.health_checks
    assert not chain.health_checks["service1"].done()
    
    # Stop monitoring
    await chain.stop()
    assert not chain.health_checks

@pytest.mark.asyncio
async def test_dependency_health_check(chain):
    """Test dependency health checking"""
    chain.add_dependency("service1", "dep1", DependencyType.CRITICAL)
    chain.add_dependency("service1", "dep2", DependencyType.REQUIRED)
    chain.add_dependency("service1", "dep3", DependencyType.OPTIONAL)
    
    # Set health states
    await chain.update_health("dep1", HealthStatus.HEALTHY)
    await chain.update_health("dep2", HealthStatus.DEGRADED)
    await chain.update_health("dep3", HealthStatus.UNHEALTHY)
    
    # Check health requirements
    assert await chain.check_dependency_health("service1", "dep1")  # Critical must be healthy
    assert await chain.check_dependency_health("service1", "dep2")  # Required can be degraded
    assert await chain.check_dependency_health("service1", "dep3")  # Optional can be any state

@pytest.mark.asyncio
async def test_metrics_collection(chain):
    """Test metrics collection"""
    chain.add_dependency("service1", "dep1", DependencyType.CRITICAL, 1.0)
    chain.add_dependency("service1", "dep2", DependencyType.REQUIRED, 0.8)
    
    await chain.update_health("dep1", HealthStatus.HEALTHY)
    await chain.update_health("dep2", HealthStatus.DEGRADED)
    
    metrics = await chain.get_metrics()
    
    assert "services" in metrics
    assert "service1" in metrics["services"]
    assert metrics["services"]["service1"]["dependency_count"] == 2
    assert "health_summary" in metrics

@pytest.mark.asyncio
async def test_concurrent_updates(chain):
    """Test concurrent health updates"""
    chain.add_dependency("service1", "dep1", DependencyType.CRITICAL)
    
    async def update_cycle():
        for _ in range(5):
            await chain.update_health("dep1", HealthStatus.HEALTHY)
            await asyncio.sleep(0.01)
            await chain.update_health("dep1", HealthStatus.UNHEALTHY)
            await asyncio.sleep(0.01)
    
    # Run multiple concurrent update cycles
    tasks = [update_cycle() for _ in range(3)]
    await asyncio.gather(*tasks)
    
    # Verify state consistency
    assert chain.health_status_cache["dep1"] in (HealthStatus.HEALTHY, HealthStatus.UNHEALTHY)

@pytest.mark.asyncio
async def test_error_handling(chain):
    """Test error handling in health check loop"""
    chain.add_dependency("service1", "dep1", DependencyType.CRITICAL)
    
    with patch.object(chain.logger, 'error') as mock_error:
        # Force an error in health check
        with patch.object(chain, '_health_check_loop', 
                         side_effect=Exception("Test error")):
            await chain.start()
            await asyncio.sleep(0.1)
            mock_error.assert_called()

@pytest.mark.asyncio
async def test_recovery_loop(chain):
    """Test recovery loop behavior"""
    chain.add_dependency("service1", "dep1", DependencyType.CRITICAL)
    
    # Start recovery
    await chain.update_health("dep1", HealthStatus.UNHEALTHY)
    await asyncio.sleep(chain.config.cascade_delay)
    
    # Verify recovery task
    assert "dep1" in chain.recovery_tasks
    assert not chain.recovery_tasks["dep1"].done()
    
    # Trigger recovery
    await chain.update_health("dep1", HealthStatus.HEALTHY)
    await asyncio.sleep(chain.config.cascade_delay)
    
    # Verify recovery completion
    assert chain.recovery_state["dep1"] 