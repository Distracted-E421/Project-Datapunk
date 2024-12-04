"""Tests for the Dependency-Aware Circuit Breaker Strategy"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from datapunk_shared.mesh.circuit_breaker.dependency_aware_strategy import (
    DependencyAwareStrategy
)
from datapunk_shared.mesh.circuit_breaker.dependency_chain import (
    DependencyType,
    HealthStatus,
    DependencyConfig
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
def strategy(config):
    return DependencyAwareStrategy(
        service_id="test_service",
        failure_threshold=3,
        success_threshold=2,
        timeout=1.0,
        half_open_timeout=0.5,
        dependency_config=config
    )

@pytest.mark.asyncio
async def test_initialization(strategy):
    """Test strategy initialization"""
    assert strategy.service_id == "test_service"
    assert strategy.failure_threshold == 3
    assert strategy.success_threshold == 2
    assert strategy.timeout == 1.0
    assert strategy.half_open_timeout == 0.5
    assert not strategy.dependency_failures

@pytest.mark.asyncio
async def test_dependency_management(strategy):
    """Test adding and removing dependencies"""
    strategy.add_dependency("dep1", DependencyType.CRITICAL)
    strategy.add_dependency("dep2", DependencyType.REQUIRED)
    
    assert "dep1" in strategy.dependency_failures
    assert "dep2" in strategy.dependency_failures
    assert strategy.dependency_failures["dep1"] == 0
    
    strategy.remove_dependency("dep1")
    assert "dep1" not in strategy.dependency_failures
    assert "dep2" in strategy.dependency_failures

@pytest.mark.asyncio
async def test_request_allowance_healthy_dependencies(strategy):
    """Test request allowance with healthy dependencies"""
    strategy.add_dependency("dep1", DependencyType.CRITICAL)
    strategy.add_dependency("dep2", DependencyType.REQUIRED)
    
    # Set dependencies as healthy
    await strategy.dependency_chain.update_health("dep1", HealthStatus.HEALTHY)
    await strategy.dependency_chain.update_health("dep2", HealthStatus.HEALTHY)
    
    assert await strategy.should_allow_request()

@pytest.mark.asyncio
async def test_request_blocking_unhealthy_critical(strategy):
    """Test request blocking with unhealthy critical dependency"""
    strategy.add_dependency("dep1", DependencyType.CRITICAL)
    strategy.add_dependency("dep2", DependencyType.REQUIRED)
    
    # Set critical dependency as unhealthy
    await strategy.dependency_chain.update_health("dep1", HealthStatus.UNHEALTHY)
    await strategy.dependency_chain.update_health("dep2", HealthStatus.HEALTHY)
    
    assert not await strategy.should_allow_request()

@pytest.mark.asyncio
async def test_request_allowance_unhealthy_required(strategy):
    """Test request allowance with unhealthy required dependency"""
    strategy.add_dependency("dep1", DependencyType.CRITICAL)
    strategy.add_dependency("dep2", DependencyType.REQUIRED)
    
    # Set required dependency as unhealthy
    await strategy.dependency_chain.update_health("dep1", HealthStatus.HEALTHY)
    await strategy.dependency_chain.update_health("dep2", HealthStatus.UNHEALTHY)
    
    # Should still allow requests if only required dependency is unhealthy
    assert await strategy.should_allow_request()

@pytest.mark.asyncio
async def test_success_handling(strategy):
    """Test success handling and health updates"""
    strategy.add_dependency("dep1", DependencyType.CRITICAL)
    strategy.dependency_failures["dep1"] = 2
    
    await strategy.record_success()
    
    assert strategy.dependency_failures["dep1"] == 0
    status = await strategy.dependency_chain.get_dependency_status(
        strategy.service_id
    )
    assert status.get(strategy.service_id) == HealthStatus.HEALTHY

@pytest.mark.asyncio
async def test_failure_handling_dependency_error(strategy):
    """Test failure handling with dependency error"""
    strategy.add_dependency("dep1", DependencyType.CRITICAL)
    
    class DependencyError(Exception):
        dependency_id = "dep1"
    
    await strategy.record_failure(DependencyError())
    
    assert strategy.dependency_failures["dep1"] == 1
    status = await strategy.dependency_chain.get_dependency_status(
        strategy.service_id
    )
    assert status.get(strategy.service_id) in (
        HealthStatus.UNHEALTHY,
        HealthStatus.DEGRADED
    )

@pytest.mark.asyncio
async def test_reset_with_healthy_dependencies(strategy):
    """Test reset with healthy dependencies"""
    strategy.add_dependency("dep1", DependencyType.CRITICAL)
    strategy.add_dependency("dep2", DependencyType.REQUIRED)
    
    # Set dependencies as healthy
    await strategy.dependency_chain.update_health("dep1", HealthStatus.HEALTHY)
    await strategy.dependency_chain.update_health("dep2", HealthStatus.HEALTHY)
    
    # Record enough successes to attempt reset
    for _ in range(strategy.success_threshold):
        await strategy.record_success()
    
    assert await strategy.attempt_reset()

@pytest.mark.asyncio
async def test_reset_blocked_by_unhealthy_dependency(strategy):
    """Test reset blocked by unhealthy dependency"""
    strategy.add_dependency("dep1", DependencyType.CRITICAL)
    strategy.add_dependency("dep2", DependencyType.REQUIRED)
    
    # Set critical dependency as unhealthy
    await strategy.dependency_chain.update_health("dep1", HealthStatus.UNHEALTHY)
    await strategy.dependency_chain.update_health("dep2", HealthStatus.HEALTHY)
    
    # Record enough successes to attempt reset
    for _ in range(strategy.success_threshold):
        await strategy.record_success()
    
    assert not await strategy.attempt_reset()

@pytest.mark.asyncio
async def test_metrics_collection(strategy):
    """Test metrics collection"""
    strategy.add_dependency("dep1", DependencyType.CRITICAL)
    strategy.add_dependency("dep2", DependencyType.REQUIRED)
    
    await strategy.record_failure(Exception())
    metrics = await strategy.get_metrics()
    
    assert "dependencies" in metrics
    assert "dependency_failures" in metrics
    assert "last_dependency_check" in metrics
    assert isinstance(metrics["dependency_failures"], dict)

@pytest.mark.asyncio
async def test_concurrent_health_updates(strategy):
    """Test concurrent health updates"""
    strategy.add_dependency("dep1", DependencyType.CRITICAL)
    
    async def update_cycle():
        for _ in range(5):
            await strategy.dependency_chain.update_health(
                "dep1",
                HealthStatus.HEALTHY
            )
            await asyncio.sleep(0.01)
            await strategy.dependency_chain.update_health(
                "dep1",
                HealthStatus.UNHEALTHY
            )
            await asyncio.sleep(0.01)
    
    # Run multiple concurrent update cycles
    tasks = [update_cycle() for _ in range(3)]
    await asyncio.gather(*tasks)
    
    # Verify state consistency
    status = await strategy.dependency_chain.get_dependency_status(
        strategy.service_id
    )
    assert status["dep1"] in (HealthStatus.HEALTHY, HealthStatus.UNHEALTHY)

@pytest.mark.asyncio
async def test_lifecycle_management(strategy):
    """Test strategy lifecycle management"""
    await strategy.start()
    assert strategy.dependency_chain.health_checks
    
    await strategy.stop()
    assert not strategy.dependency_chain.health_checks
    assert not strategy.dependency_chain.recovery_tasks

@pytest.mark.asyncio
async def test_cascading_failure_handling(strategy):
    """Test cascading failure handling"""
    strategy.add_dependency("dep1", DependencyType.CRITICAL)
    strategy.add_dependency("dep2", DependencyType.REQUIRED, impact_score=0.8)
    
    # Simulate cascading failures
    for _ in range(strategy.failure_threshold + 1):
        await strategy.record_failure(Exception())
    
    # Verify impact on dependencies
    status = await strategy.dependency_chain.get_dependency_status(
        strategy.service_id
    )
    assert status.get(strategy.service_id) == HealthStatus.UNHEALTHY 