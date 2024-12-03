import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.health import (
    HealthChecker,
    HealthConfig,
    HealthCheck,
    HealthStatus,
    HealthError
)

@pytest.fixture
def health_config():
    return HealthConfig(
        name="test_health",
        checks=[
            HealthCheck(
                name="database",
                type="connection",
                target="postgresql://localhost:5432/test",
                timeout=5.0,
                interval=30.0
            ),
            HealthCheck(
                name="redis",
                type="connection",
                target="redis://localhost:6379",
                timeout=2.0,
                interval=15.0
            ),
            HealthCheck(
                name="disk_space",
                type="resource",
                target="/",
                threshold=90.0,  # Percentage
                interval=60.0
            )
        ],
        metrics_enabled=True,
        notification_enabled=True
    )

@pytest.fixture
async def health_checker(health_config):
    checker = HealthChecker(health_config)
    await checker.initialize()
    return checker

@pytest.mark.asyncio
async def test_checker_initialization(health_checker, health_config):
    """Test health checker initialization"""
    assert health_checker.config == health_config
    assert health_checker.is_initialized
    assert len(health_checker.checks) == len(health_config.checks)

@pytest.mark.asyncio
async def test_connection_check(health_checker):
    """Test connection health check"""
    # Mock successful connection
    with patch('socket.socket') as mock_socket:
        mock_socket.return_value.connect_ex.return_value = 0
        
        result = await health_checker.check_connection("database")
        assert result.status == HealthStatus.HEALTHY
        assert result.latency is not None

@pytest.mark.asyncio
async def test_resource_check(health_checker):
    """Test resource health check"""
    # Mock disk space check
    with patch('psutil.disk_usage') as mock_disk:
        mock_disk.return_value.percent = 80.0  # Below threshold
        
        result = await health_checker.check_resource("disk_space")
        assert result.status == HealthStatus.HEALTHY
        assert result.metrics["usage_percent"] == 80.0

@pytest.mark.asyncio
async def test_health_metrics(health_checker):
    """Test health check metrics"""
    metrics = []
    health_checker.set_metrics_callback(metrics.append)
    
    await health_checker.check_all()
    
    assert len(metrics) > 0
    assert any(m["type"] == "health_check" for m in metrics)
    assert any(m["type"] == "check_latency" for m in metrics)

@pytest.mark.asyncio
async def test_health_notifications(health_checker):
    """Test health check notifications"""
    notification_handler = AsyncMock()
    health_checker.set_notification_handler(notification_handler)
    
    # Simulate unhealthy state
    with patch('socket.socket') as mock_socket:
        mock_socket.return_value.connect_ex.return_value = 1  # Connection failed
        
        await health_checker.check_connection("database")
        
        notification_handler.assert_called_once()

@pytest.mark.asyncio
async def test_check_scheduling(health_checker):
    """Test health check scheduling"""
    check_results = []
    
    async def mock_check(check_name):
        check_results.append(check_name)
        return HealthStatus.HEALTHY
    
    health_checker.add_check_handler(mock_check)
    
    # Start scheduler
    await health_checker.start_scheduled_checks()
    await asyncio.sleep(0.1)  # Allow scheduler to run
    
    assert len(check_results) > 0
    
    # Stop scheduler
    await health_checker.stop_scheduled_checks()

@pytest.mark.asyncio
async def test_custom_health_check(health_checker):
    """Test custom health check"""
    # Add custom check
    async def check_memory(params):
        import psutil
        memory = psutil.virtual_memory()
        return memory.percent < params.get("threshold", 90)
    
    health_checker.add_check(
        HealthCheck(
            name="memory",
            type="custom",
            params={"threshold": 90},
            handler=check_memory
        )
    )
    
    result = await health_checker.run_check("memory")
    assert result.status in [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY]

@pytest.mark.asyncio
async def test_health_history(health_checker):
    """Test health check history"""
    # Perform multiple checks
    for _ in range(3):
        await health_checker.check_all()
    
    history = health_checker.get_check_history()
    
    assert len(history) > 0
    assert all(isinstance(entry.timestamp, datetime) for entry in history)
    assert all(hasattr(entry, 'status') for entry in history)

@pytest.mark.asyncio
async def test_health_aggregation(health_checker):
    """Test health status aggregation"""
    # Mock check results
    mock_results = {
        "database": HealthStatus.HEALTHY,
        "redis": HealthStatus.DEGRADED,
        "disk_space": HealthStatus.HEALTHY
    }
    
    with patch.object(health_checker, 'check_all') as mock_check:
        mock_check.return_value = mock_results
        
        aggregate_status = await health_checker.get_aggregate_status()
        assert aggregate_status == HealthStatus.DEGRADED

@pytest.mark.asyncio
async def test_error_handling(health_checker):
    """Test error handling"""
    # Test with invalid check name
    with pytest.raises(HealthError):
        await health_checker.run_check("non_existent")
    
    # Test with invalid check type
    with pytest.raises(HealthError):
        health_checker.add_check(
            HealthCheck(
                name="invalid",
                type="invalid_type",
                target="test"
            )
        )

@pytest.mark.asyncio
async def test_check_dependencies(health_checker):
    """Test health check dependencies"""
    # Add dependent checks
    health_checker.add_check(
        HealthCheck(
            name="api_server",
            type="connection",
            target="http://localhost:8000",
            dependencies=["database", "redis"]
        )
    )
    
    # Mock dependency results
    async def mock_check(check_name):
        if check_name == "database":
            return HealthStatus.UNHEALTHY
        return HealthStatus.HEALTHY
    
    health_checker.add_check_handler(mock_check)
    
    result = await health_checker.run_check("api_server")
    assert result.status == HealthStatus.UNHEALTHY  # Due to database dependency

@pytest.mark.asyncio
async def test_health_reporting(health_checker):
    """Test health report generation"""
    # Generate health report
    report = await health_checker.generate_report()
    
    assert "timestamp" in report
    assert "checks" in report
    assert "aggregate_status" in report
    assert isinstance(report["checks"], dict)

@pytest.mark.asyncio
async def test_check_timeout(health_checker):
    """Test health check timeout"""
    # Add slow check
    async def slow_check(params):
        await asyncio.sleep(2.0)
        return True
    
    health_checker.add_check(
        HealthCheck(
            name="slow_check",
            type="custom",
            timeout=1.0,
            handler=slow_check
        )
    )
    
    result = await health_checker.run_check("slow_check")
    assert result.status == HealthStatus.UNKNOWN
    assert "timeout" in str(result.error) 