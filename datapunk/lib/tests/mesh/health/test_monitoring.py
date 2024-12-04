import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.health import (
    HealthMonitor,
    MonitorConfig,
    HealthStatus,
    MonitoredService,
    HealthAlert,
    TrendAnalysis
)

@pytest.fixture
def monitor_config():
    return MonitorConfig(
        check_interval=5,  # seconds
        alert_threshold=3,
        trend_window=300,  # 5 minutes
        retention_period=3600  # 1 hour
    )

@pytest.fixture
def health_monitor(monitor_config):
    return HealthMonitor(config=monitor_config)

@pytest.fixture
def sample_services():
    return [
        MonitoredService(
            name="api-service",
            endpoint="http://api:8080/health",
            check_interval=5,
            timeout=2,
            expected_status=200
        ),
        MonitoredService(
            name="database",
            endpoint="postgresql://db:5432",
            check_interval=10,
            timeout=3,
            custom_check=True
        )
    ]

@pytest.mark.asyncio
async def test_monitor_initialization(health_monitor, monitor_config):
    assert health_monitor.config == monitor_config
    assert health_monitor.is_initialized
    assert len(health_monitor.services) == 0

@pytest.mark.asyncio
async def test_service_registration(health_monitor, sample_services):
    for service in sample_services:
        await health_monitor.register_service(service)
    
    assert len(health_monitor.services) == len(sample_services)
    assert all(s.name in health_monitor.services for s in sample_services)

@pytest.mark.asyncio
async def test_health_check_execution(health_monitor):
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"status": "healthy"}
        )
        mock_get.return_value.__aenter__.return_value = mock_response
        
        service = MonitoredService(
            name="test-service",
            endpoint="http://test:8080/health",
            check_interval=5
        )
        
        await health_monitor.register_service(service)
        result = await health_monitor.check_service_health("test-service")
        
        assert result.status == HealthStatus.HEALTHY

@pytest.mark.asyncio
async def test_custom_health_check(health_monitor):
    async def custom_check():
        return {
            "status": "healthy",
            "metrics": {"connections": 10}
        }
    
    service = MonitoredService(
        name="custom-service",
        endpoint="custom://service",
        check_interval=5,
        custom_check=custom_check
    )
    
    await health_monitor.register_service(service)
    result = await health_monitor.check_service_health("custom-service")
    
    assert result.status == HealthStatus.HEALTHY
    assert result.details["metrics"]["connections"] == 10

@pytest.mark.asyncio
async def test_alert_generation(health_monitor):
    alerts = []
    
    def alert_handler(alert: HealthAlert):
        alerts.append(alert)
    
    health_monitor.on_alert(alert_handler)
    
    # Register service that will fail
    service = MonitoredService(
        name="failing-service",
        endpoint="http://failing:8080/health",
        check_interval=1
    )
    
    with patch('aiohttp.ClientSession.get', side_effect=Exception("Connection failed")):
        await health_monitor.register_service(service)
        
        # Execute multiple failed checks
        for _ in range(4):  # More than alert_threshold
            await health_monitor.check_service_health("failing-service")
        
        assert len(alerts) > 0
        assert alerts[0].service_name == "failing-service"
        assert alerts[0].severity == "critical"

@pytest.mark.asyncio
async def test_trend_analysis(health_monitor):
    service = MonitoredService(
        name="trend-service",
        endpoint="http://trend:8080/health",
        check_interval=1
    )
    
    await health_monitor.register_service(service)
    
    # Record multiple health checks with varying response times
    times = [50, 100, 150, 200, 250]  # ms
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        for time_ms in times:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"latency_ms": time_ms}
            )
            mock_get.return_value.__aenter__.return_value = mock_response
            
            await health_monitor.check_service_health("trend-service")
    
    trend = await health_monitor.analyze_trends("trend-service")
    assert isinstance(trend, TrendAnalysis)
    assert trend.is_degrading

@pytest.mark.asyncio
async def test_status_aggregation(health_monitor, sample_services):
    for service in sample_services:
        await health_monitor.register_service(service)
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"status": "healthy"}
        )
        mock_get.return_value.__aenter__.return_value = mock_response
        
        status = await health_monitor.get_overall_status()
        assert status.total_services == len(sample_services)
        assert status.healthy_services == len(sample_services)

@pytest.mark.asyncio
async def test_metrics_collection(health_monitor):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        service = MonitoredService(
            name="metrics-service",
            endpoint="http://metrics:8080/health",
            check_interval=5
        )
        
        await health_monitor.register_service(service)
        await health_monitor.check_service_health("metrics-service")
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_gauge.assert_called()

@pytest.mark.asyncio
async def test_service_dependencies(health_monitor):
    services_checked = []
    
    async def check_service(name):
        services_checked.append(name)
        return {"status": "healthy"}
    
    # Create services with dependencies
    primary = MonitoredService(
        name="primary",
        endpoint="http://primary:8080/health",
        check_interval=5,
        custom_check=lambda: check_service("primary")
    )
    
    dependent = MonitoredService(
        name="dependent",
        endpoint="http://dependent:8080/health",
        check_interval=5,
        dependencies=["primary"],
        custom_check=lambda: check_service("dependent")
    )
    
    await health_monitor.register_service(primary)
    await health_monitor.register_service(dependent)
    
    await health_monitor.check_service_health("dependent")
    assert services_checked == ["primary", "dependent"]

@pytest.mark.asyncio
async def test_health_history(health_monitor):
    service = MonitoredService(
        name="history-service",
        endpoint="http://history:8080/health",
        check_interval=5
    )
    
    await health_monitor.register_service(service)
    
    # Record multiple health checks
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"status": "healthy"}
        )
        mock_get.return_value.__aenter__.return_value = mock_response
        
        for _ in range(5):
            await health_monitor.check_service_health("history-service")
    
    history = await health_monitor.get_service_history("history-service")
    assert len(history) == 5
    assert all(check.status == HealthStatus.HEALTHY for check in history)

@pytest.mark.asyncio
async def test_monitor_persistence(health_monitor):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        await health_monitor.save_state()
        mock_file.write.assert_called_once()
        
        await health_monitor.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_concurrent_monitoring(health_monitor, sample_services):
    for service in sample_services:
        await health_monitor.register_service(service)
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"status": "healthy"}
        )
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Check all services concurrently
        results = await asyncio.gather(*[
            health_monitor.check_service_health(service.name)
            for service in sample_services
        ])
        
        assert len(results) == len(sample_services)
        assert all(r.status == HealthStatus.HEALTHY for r in results)

@pytest.mark.asyncio
async def test_monitor_cleanup(health_monitor):
    service = MonitoredService(
        name="cleanup-service",
        endpoint="http://cleanup:8080/health",
        check_interval=5
    )
    
    await health_monitor.register_service(service)
    
    # Record some health checks
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        
        await health_monitor.check_service_health("cleanup-service")
    
    # Mark for cleanup and run cleanup
    await health_monitor.mark_for_cleanup("cleanup-service")
    await health_monitor.cleanup()
    
    assert "cleanup-service" not in health_monitor.services