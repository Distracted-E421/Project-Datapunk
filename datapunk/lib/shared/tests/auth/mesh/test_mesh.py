"""
Mesh Module Tests
------------

Tests the service mesh system including:
- Circuit breaker functionality
- Service discovery
- Load balancing
- Health monitoring
- Mesh configuration

Run with: pytest -v test_mesh.py
"""

import pytest
from datetime import datetime, timedelta
import json
from unittest.mock import AsyncMock, Mock, patch

from datapunk_shared.auth.mesh import (
    CircuitBreaker,
    ServiceDiscovery,
    LoadBalancer,
    HealthMonitor,
    MeshConfig
)

# Test Fixtures

@pytest.fixture
def storage_client():
    """Mock storage client for testing."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.set = AsyncMock()
    client.delete = AsyncMock()
    return client

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.gauge = AsyncMock()
    client.timing = AsyncMock()
    return client

@pytest.fixture
def mesh_config():
    """Create mesh configuration for testing."""
    return MeshConfig(
        service_name="test_service",
        discovery_enabled=True,
        load_balancing_enabled=True,
        health_check_interval=timedelta(seconds=30)
    )

@pytest.fixture
def circuit_breaker(storage_client, metrics_client):
    """Create circuit breaker for testing."""
    return CircuitBreaker(
        storage=storage_client,
        metrics=metrics_client,
        failure_threshold=5,
        reset_timeout=timedelta(seconds=60)
    )

@pytest.fixture
def service_discovery():
    """Create service discovery for testing."""
    return ServiceDiscovery()

@pytest.fixture
def load_balancer():
    """Create load balancer for testing."""
    return LoadBalancer()

@pytest.fixture
def health_monitor():
    """Create health monitor for testing."""
    return HealthMonitor()

# Circuit Breaker Tests

@pytest.mark.asyncio
async def test_circuit_breaker_states(circuit_breaker):
    """Test circuit breaker state transitions."""
    # Initial state
    assert circuit_breaker.state == "closed"
    
    # Record failures
    for _ in range(5):
        await circuit_breaker.record_failure()
    
    # Should be open
    assert circuit_breaker.state == "open"
    
    # Wait for timeout
    await asyncio.sleep(1)
    
    # Should be half-open
    assert circuit_breaker.state == "half-open"
    
    # Record success
    await circuit_breaker.record_success()
    
    # Should be closed
    assert circuit_breaker.state == "closed"

@pytest.mark.asyncio
async def test_circuit_breaker_protection(circuit_breaker):
    """Test circuit breaker protection."""
    # Open circuit
    for _ in range(5):
        await circuit_breaker.record_failure()
    
    # Should prevent execution
    with pytest.raises(CircuitBreakerError):
        await circuit_breaker.execute(lambda: "test")
    
    # Wait for reset
    await asyncio.sleep(1)
    
    # Should allow execution in half-open state
    result = await circuit_breaker.execute(lambda: "test")
    assert result == "test"

# Service Discovery Tests

@pytest.mark.asyncio
async def test_service_registration(service_discovery):
    """Test service registration."""
    # Register service
    service = await service_discovery.register_service({
        "name": "test_service",
        "host": "localhost",
        "port": 8080,
        "metadata": {
            "version": "1.0.0",
            "environment": "test"
        }
    })
    
    assert service.id is not None
    assert service.name == "test_service"
    assert service.host == "localhost"
    assert service.port == 8080

@pytest.mark.asyncio
async def test_service_discovery(service_discovery):
    """Test service discovery."""
    # Register multiple services
    services = [
        {
            "name": "test_service",
            "host": f"host{i}",
            "port": 8080 + i
        }
        for i in range(3)
    ]
    
    for service in services:
        await service_discovery.register_service(service)
    
    # Discover services
    instances = await service_discovery.discover_service("test_service")
    assert len(instances) == 3
    assert all(i.name == "test_service" for i in instances)

# Load Balancer Tests

@pytest.mark.asyncio
async def test_load_balancing(load_balancer):
    """Test load balancing strategies."""
    # Add services
    services = [
        {
            "id": f"service{i}",
            "weight": 1,
            "health": 1.0
        }
        for i in range(3)
    ]
    
    for service in services:
        load_balancer.add_service(service)
    
    # Test round-robin
    selected = [
        await load_balancer.select_service()
        for _ in range(6)
    ]
    assert len(set(s.id for s in selected)) == 3
    
    # Test weighted
    load_balancer.strategy = "weighted"
    services[0]["weight"] = 2
    selected = [
        await load_balancer.select_service()
        for _ in range(6)
    ]
    assert sum(1 for s in selected if s.id == "service0") > 2

@pytest.mark.asyncio
async def test_load_balancer_health(load_balancer):
    """Test load balancer health awareness."""
    # Add services with different health
    services = [
        {"id": "healthy", "health": 1.0},
        {"id": "degraded", "health": 0.5},
        {"id": "unhealthy", "health": 0.0}
    ]
    
    for service in services:
        load_balancer.add_service(service)
    
    # Should prefer healthy services
    selected = [
        await load_balancer.select_service()
        for _ in range(10)
    ]
    assert all(s.id != "unhealthy" for s in selected)
    assert sum(1 for s in selected if s.id == "healthy") > sum(1 for s in selected if s.id == "degraded")

# Health Monitoring Tests

@pytest.mark.asyncio
async def test_health_checks(health_monitor):
    """Test health check execution."""
    # Add health check
    check = await health_monitor.add_check({
        "name": "test_check",
        "endpoint": "http://localhost:8080/health",
        "interval": timedelta(seconds=30),
        "timeout": timedelta(seconds=5)
    })
    
    assert check.name == "test_check"
    assert check.status == "pending"
    
    # Execute check
    result = await health_monitor.execute_check(check.id)
    assert result.success in [True, False]
    assert result.latency is not None

@pytest.mark.asyncio
async def test_health_aggregation(health_monitor):
    """Test health status aggregation."""
    # Add multiple checks
    checks = [
        {
            "name": f"check{i}",
            "weight": 1.0
        }
        for i in range(3)
    ]
    
    for check in checks:
        await health_monitor.add_check(check)
    
    # Set check results
    await health_monitor.update_check_status("check0", True)
    await health_monitor.update_check_status("check1", True)
    await health_monitor.update_check_status("check2", False)
    
    # Get aggregate health
    health = await health_monitor.get_aggregate_health()
    assert 0.5 < health < 0.8  # Should reflect 2/3 healthy

# Configuration Tests

def test_mesh_configuration():
    """Test mesh configuration."""
    config = MeshConfig(
        service_name="test_service",
        discovery_enabled=True,
        load_balancing_enabled=True,
        health_check_interval=timedelta(seconds=30),
        circuit_breaker_config={
            "failure_threshold": 5,
            "reset_timeout": 60
        }
    )
    
    assert config.service_name == "test_service"
    assert config.discovery_enabled is True
    assert config.load_balancing_enabled is True
    assert config.health_check_interval.total_seconds() == 30

def test_config_validation():
    """Test configuration validation."""
    # Invalid service name
    with pytest.raises(ValueError):
        MeshConfig(service_name="")
    
    # Invalid interval
    with pytest.raises(ValueError):
        MeshConfig(
            service_name="test",
            health_check_interval=timedelta(seconds=-1)
        )

# Performance Tests

@pytest.mark.asyncio
async def test_circuit_breaker_performance(circuit_breaker):
    """Test circuit breaker performance."""
    # Generate test operations
    operations = [
        lambda: f"operation_{i}"
        for i in range(1000)
    ]
    
    # Measure execution time
    start_time = datetime.utcnow()
    results = await asyncio.gather(*[
        circuit_breaker.execute(op)
        for op in operations
    ])
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 2.0  # Should process 1000 operations within 2 seconds
    assert len(results) == 1000

@pytest.mark.asyncio
async def test_service_discovery_performance(service_discovery):
    """Test service discovery performance."""
    # Register many services
    services = [
        {
            "name": "test_service",
            "host": f"host{i}",
            "port": 8080 + i
        }
        for i in range(100)
    ]
    
    # Measure registration time
    start_time = datetime.utcnow()
    registered = await asyncio.gather(*[
        service_discovery.register_service(service)
        for service in services
    ])
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 1.0  # Should register 100 services within 1 second
    assert len(registered) == 100 