"""Tests for the Advanced Circuit Breaker"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from datapunk_shared.mesh.circuit_breaker.circuit_breaker_advanced import (
    AdvancedCircuitBreaker
)
from datapunk_shared.mesh.circuit_breaker.dependency_chain import (
    DependencyConfig,
    DependencyType
)

@pytest.fixture
def circuit_breaker():
    return AdvancedCircuitBreaker(
        service_id="test_service",
        strategy_type="basic",
        failure_threshold=3,
        success_threshold=2,
        timeout=1.0,
        half_open_timeout=0.5
    )

@pytest.fixture
def dependency_circuit_breaker():
    return AdvancedCircuitBreaker(
        service_id="test_service",
        strategy_type="dependency",
        failure_threshold=3,
        success_threshold=2,
        timeout=1.0,
        half_open_timeout=0.5,
        dependency_config=DependencyConfig(
            health_check_interval=0.1,
            failure_threshold=2,
            recovery_threshold=1,
            cascade_delay=0.1,
            max_retry_interval=1.0
        )
    )

@pytest.mark.asyncio
async def test_initialization(circuit_breaker):
    """Test circuit breaker initialization"""
    assert circuit_breaker.service_id == "test_service"
    assert circuit_breaker.strategy is not None
    assert circuit_breaker.metrics is not None
    assert circuit_breaker.timeout_manager is not None
    assert circuit_breaker.failure_predictor is not None
    assert circuit_breaker.priority_manager is not None
    assert circuit_breaker.recovery_manager is not None
    assert circuit_breaker.retry_manager is not None
    assert circuit_breaker.health_manager is not None
    assert circuit_breaker.discovery_manager is not None

@pytest.mark.asyncio
async def test_lifecycle_management(circuit_breaker):
    """Test start and stop functionality"""
    await circuit_breaker.start()
    # Verify components are started
    
    await circuit_breaker.stop()
    # Verify components are stopped

@pytest.mark.asyncio
async def test_request_allowance_basic(circuit_breaker):
    """Test request allowance with basic strategy"""
    await circuit_breaker.start()
    
    # Should allow requests initially
    assert await circuit_breaker.should_allow_request()
    
    # Record failures
    for _ in range(circuit_breaker.strategy.failure_threshold):
        await circuit_breaker.record_failure()
    
    # Should block requests after threshold
    assert not await circuit_breaker.should_allow_request()
    
    await circuit_breaker.stop()

@pytest.mark.asyncio
async def test_request_allowance_dependency(dependency_circuit_breaker):
    """Test request allowance with dependency strategy"""
    await dependency_circuit_breaker.start()
    
    # Add dependencies
    dependency_circuit_breaker.add_dependency(
        "dep1",
        DependencyType.CRITICAL.value
    )
    dependency_circuit_breaker.add_dependency(
        "dep2",
        DependencyType.REQUIRED.value
    )
    
    # Should allow requests with healthy dependencies
    assert await dependency_circuit_breaker.should_allow_request()
    
    # Record failures for critical dependency
    for _ in range(dependency_circuit_breaker.strategy.failure_threshold):
        await dependency_circuit_breaker.record_failure(
            Exception("dep1 failure")
        )
    
    # Should block requests with unhealthy critical dependency
    assert not await dependency_circuit_breaker.should_allow_request()
    
    await dependency_circuit_breaker.stop()

@pytest.mark.asyncio
async def test_failure_prediction_blocking(circuit_breaker):
    """Test request blocking by failure prediction"""
    await circuit_breaker.start()
    
    # Mock failure prediction
    with patch.object(
        circuit_breaker.failure_predictor,
        'predict_failure',
        return_value=True
    ):
        assert not await circuit_breaker.should_allow_request()
    
    await circuit_breaker.stop()

@pytest.mark.asyncio
async def test_resource_constraint_blocking(circuit_breaker):
    """Test request blocking by resource constraints"""
    await circuit_breaker.start()
    
    # Mock resource check
    with patch.object(
        circuit_breaker.priority_manager,
        'check_resources',
        return_value=False
    ):
        assert not await circuit_breaker.should_allow_request()
    
    await circuit_breaker.stop()

@pytest.mark.asyncio
async def test_health_check_blocking(circuit_breaker):
    """Test request blocking by health check"""
    await circuit_breaker.start()
    
    # Mock health check
    with patch.object(
        circuit_breaker.health_manager,
        'is_healthy',
        return_value=False
    ):
        assert not await circuit_breaker.should_allow_request()
    
    await circuit_breaker.stop()

@pytest.mark.asyncio
async def test_service_discovery_blocking(circuit_breaker):
    """Test request blocking by service discovery"""
    await circuit_breaker.start()
    
    # Mock service discovery
    with patch.object(
        circuit_breaker.discovery_manager,
        'is_available',
        return_value=False
    ):
        assert not await circuit_breaker.should_allow_request()
    
    await circuit_breaker.stop()

@pytest.mark.asyncio
async def test_metrics_collection(circuit_breaker):
    """Test metrics collection from all components"""
    await circuit_breaker.start()
    
    # Record some activity
    await circuit_breaker.record_success()
    await circuit_breaker.record_failure()
    
    # Get metrics
    metrics = await circuit_breaker.get_metrics()
    
    # Verify metrics structure
    assert "strategy" in metrics
    assert "timeout" in metrics
    assert "prediction" in metrics
    assert "priority" in metrics
    assert "recovery" in metrics
    assert "retry" in metrics
    assert "health" in metrics
    assert "discovery" in metrics
    
    await circuit_breaker.stop()

@pytest.mark.asyncio
async def test_dependency_management(dependency_circuit_breaker):
    """Test dependency management functionality"""
    await dependency_circuit_breaker.start()
    
    # Add dependency
    dependency_circuit_breaker.add_dependency(
        "dep1",
        DependencyType.CRITICAL.value,
        impact_score=1.0
    )
    
    # Record dependency failure
    await dependency_circuit_breaker.record_failure(
        Exception("dep1 failure")
    )
    
    # Remove dependency
    dependency_circuit_breaker.remove_dependency("dep1")
    
    # Verify dependency removal
    with pytest.raises(RuntimeError):
        dependency_circuit_breaker.remove_dependency("dep1")
    
    await dependency_circuit_breaker.stop()

@pytest.mark.asyncio
async def test_concurrent_requests(circuit_breaker):
    """Test concurrent request handling"""
    await circuit_breaker.start()
    
    async def make_request():
        if await circuit_breaker.should_allow_request():
            await circuit_breaker.record_success()
            return True
        return False
    
    # Run multiple concurrent requests
    tasks = [make_request() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    # Verify results
    assert any(results)  # At least some requests should succeed
    
    await circuit_breaker.stop()

@pytest.mark.asyncio
async def test_strategy_switching():
    """Test switching between different strategies"""
    # Test basic strategy
    basic_breaker = AdvancedCircuitBreaker(
        service_id="test_service",
        strategy_type="basic"
    )
    assert not isinstance(basic_breaker.strategy, DependencyAwareStrategy)
    
    # Test dependency strategy
    dep_breaker = AdvancedCircuitBreaker(
        service_id="test_service",
        strategy_type="dependency"
    )
    assert isinstance(dep_breaker.strategy, DependencyAwareStrategy)
    
    # Test invalid strategy
    with pytest.raises(ValueError):
        AdvancedCircuitBreaker(
            service_id="test_service",
            strategy_type="invalid"
        )