import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.monitoring.health import (
    HealthMonitor,
    HealthConfig,
    HealthStatus,
    HealthCheck,
    HealthCheckResult
)
from datapunk_shared.monitoring import MetricsClient
from datapunk_shared.tracing import TracingManager

@pytest.fixture
def health_config():
    return HealthConfig(
        name="test_health",
        check_interval=5,  # seconds
        failure_threshold=3,
        recovery_threshold=2,
        checks=[
            HealthCheck(
                name="database",
                type="connection",
                endpoint="postgresql://localhost:5432",
                timeout=5
            ),
            HealthCheck(
                name="redis",
                type="connection",
                endpoint="redis://localhost:6379",
                timeout=3
            ),
            HealthCheck(
                name="api",
                type="http",
                endpoint="http://localhost:8000/health",
                timeout=2
            )
        ]
    )

@pytest.fixture
def mock_metrics():
    return MagicMock(spec=MetricsClient)

@pytest.fixture
def mock_tracing():
    return MagicMock(spec=TracingManager)

@pytest.fixture
async def health_monitor(health_config, mock_metrics, mock_tracing):
    monitor = HealthMonitor(health_config, mock_metrics, mock_tracing)
    await monitor.initialize()
    return monitor

@pytest.mark.asyncio
async def test_monitor_initialization(health_monitor, health_config):
    """Test health monitor initialization"""
    assert health_monitor.config == health_config
    assert not health_monitor.is_stopped
    assert len(health_monitor.checks) == len(health_config.checks)

@pytest.mark.asyncio
async def test_database_health_check(health_monitor):
    """Test database health check"""
    with patch('asyncpg.connect') as mock_connect:
        # Mock successful connection
        mock_connect.return_value = AsyncMock()
        
        result = await health_monitor.check_database("database")
        
        assert result.status == HealthStatus.HEALTHY
        assert result.latency > 0
        
        # Mock connection failure
        mock_connect.side_effect = Exception("Connection failed")
        
        result = await health_monitor.check_database("database")
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "Connection failed" in result.message

@pytest.mark.asyncio
async def test_redis_health_check(health_monitor):
    """Test Redis health check"""
    with patch('aioredis.Redis.from_url') as mock_redis:
        # Mock successful connection
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client
        
        result = await health_monitor.check_redis("redis")
        
        assert result.status == HealthStatus.HEALTHY
        assert result.latency > 0
        
        # Mock connection failure
        mock_client.ping.side_effect = Exception("Redis unavailable")
        
        result = await health_monitor.check_redis("redis")
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "Redis unavailable" in result.message

@pytest.mark.asyncio
async def test_http_health_check(health_monitor):
    """Test HTTP health check"""
    with patch('aiohttp.ClientSession.get') as mock_get:
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value = mock_response
        
        result = await health_monitor.check_http("api")
        
        assert result.status == HealthStatus.HEALTHY
        assert result.latency > 0
        
        # Mock failed response
        mock_response.status = 500
        
        result = await health_monitor.check_http("api")
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "HTTP 500" in result.message

@pytest.mark.asyncio
async def test_failure_threshold(health_monitor):
    """Test failure threshold handling"""
    check_name = "database"
    
    # Simulate multiple failures
    for _ in range(health_monitor.config.failure_threshold + 1):
        result = HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message="Test failure",
            latency=0.1
        )
        await health_monitor.record_check_result(check_name, result)
    
    # Verify degraded status
    status = await health_monitor.get_check_status(check_name)
    assert status == HealthStatus.DEGRADED
    
    # Verify metrics
    health_monitor.metrics.increment.assert_called_with(
        'health_check_failures_total',
        {'monitor': health_monitor.config.name, 'check': check_name}
    )

@pytest.mark.asyncio
async def test_recovery_threshold(health_monitor):
    """Test recovery threshold handling"""
    check_name = "database"
    
    # First make it fail
    for _ in range(health_monitor.config.failure_threshold + 1):
        result = HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            message="Test failure",
            latency=0.1
        )
        await health_monitor.record_check_result(check_name, result)
    
    # Then recover
    for _ in range(health_monitor.config.recovery_threshold):
        result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="Recovered",
            latency=0.1
        )
        await health_monitor.record_check_result(check_name, result)
    
    # Verify recovered status
    status = await health_monitor.get_check_status(check_name)
    assert status == HealthStatus.HEALTHY
    
    # Verify metrics
    health_monitor.metrics.increment.assert_called_with(
        'health_check_recoveries_total',
        {'monitor': health_monitor.config.name, 'check': check_name}
    )

@pytest.mark.asyncio
async def test_health_check_timeout(health_monitor):
    """Test health check timeout handling"""
    with patch('asyncio.wait_for') as mock_wait:
        # Mock timeout
        mock_wait.side_effect = asyncio.TimeoutError()
        
        result = await health_monitor.run_check("database")
        
        assert result.status == HealthStatus.UNHEALTHY
        assert "Timeout" in result.message
        
        # Verify metrics
        health_monitor.metrics.increment.assert_called_with(
            'health_check_timeouts_total',
            {'monitor': health_monitor.config.name, 'check': 'database'}
        )

@pytest.mark.asyncio
async def test_health_check_history(health_monitor):
    """Test health check history tracking"""
    check_name = "database"
    
    # Record multiple results
    results = [
        HealthCheckResult(status=HealthStatus.HEALTHY, message="OK", latency=0.1),
        HealthCheckResult(status=HealthStatus.UNHEALTHY, message="Failed", latency=0.2),
        HealthCheckResult(status=HealthStatus.HEALTHY, message="Recovered", latency=0.1)
    ]
    
    for result in results:
        await health_monitor.record_check_result(check_name, result)
    
    # Get history
    history = await health_monitor.get_check_history(check_name)
    
    assert len(history) == len(results)
    assert [r.status for r in history] == [r.status for r in results]

@pytest.mark.asyncio
async def test_overall_health_status(health_monitor):
    """Test overall health status calculation"""
    # Make some checks fail
    await health_monitor.record_check_result(
        "database",
        HealthCheckResult(status=HealthStatus.UNHEALTHY, message="Failed", latency=0.1)
    )
    await health_monitor.record_check_result(
        "redis",
        HealthCheckResult(status=HealthStatus.HEALTHY, message="OK", latency=0.1)
    )
    
    # Get overall status
    status = await health_monitor.get_overall_status()
    
    assert status == HealthStatus.DEGRADED
    
    # Verify metrics
    health_monitor.metrics.gauge.assert_called_with(
        'overall_health_status',
        HealthStatus.DEGRADED.value,
        {'monitor': health_monitor.config.name}
    )

@pytest.mark.asyncio
async def test_health_check_latency(health_monitor):
    """Test health check latency tracking"""
    check_name = "database"
    latency = 0.1
    
    result = HealthCheckResult(
        status=HealthStatus.HEALTHY,
        message="OK",
        latency=latency
    )
    await health_monitor.record_check_result(check_name, result)
    
    # Verify latency metrics
    health_monitor.metrics.histogram.assert_called_with(
        'health_check_latency_seconds',
        {'monitor': health_monitor.config.name, 'check': check_name},
        value=latency
    )

@pytest.mark.asyncio
async def test_tracing_integration(health_monitor):
    """Test tracing integration"""
    check_name = "database"
    result = HealthCheckResult(
        status=HealthStatus.HEALTHY,
        message="OK",
        latency=0.1
    )
    
    await health_monitor.record_check_result(check_name, result)
    
    # Verify tracing attributes
    health_monitor.tracing.set_attribute.assert_any_call(
        'health_check.name', check_name
    )
    health_monitor.tracing.set_attribute.assert_any_call(
        'health_check.status', HealthStatus.HEALTHY.value
    )
    health_monitor.tracing.set_attribute.assert_any_call(
        'health_check.latency', 0.1
    ) 