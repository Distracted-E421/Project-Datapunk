import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.health import (
    HealthCheck,
    HealthCheckConfig,
    HealthStatus,
    CheckResult,
    HealthError
)

@pytest.fixture
def health_config():
    return HealthCheckConfig(
        check_interval=5,  # seconds
        timeout=2,  # seconds
        failure_threshold=3,
        success_threshold=2,
        retry_delay=1  # seconds
    )

@pytest.fixture
def health_check(health_config):
    return HealthCheck(config=health_config)

@pytest.fixture
def sample_checks():
    async def database_check():
        return CheckResult(
            name="database",
            status=HealthStatus.HEALTHY,
            details={"latency_ms": 50}
        )
    
    async def api_check():
        return CheckResult(
            name="api",
            status=HealthStatus.HEALTHY,
            details={"endpoint": "/health"}
        )
    
    return {
        "database": database_check,
        "api": api_check
    }

@pytest.mark.asyncio
async def test_health_check_initialization(health_check, health_config):
    assert health_check.config == health_config
    assert health_check.is_initialized
    assert len(health_check.checks) == 0

@pytest.mark.asyncio
async def test_check_registration(health_check, sample_checks):
    for name, check in sample_checks.items():
        await health_check.register_check(name, check)
    
    assert len(health_check.checks) == len(sample_checks)
    assert all(name in health_check.checks for name in sample_checks)

@pytest.mark.asyncio
async def test_check_execution(health_check, sample_checks):
    await health_check.register_check("database", sample_checks["database"])
    
    result = await health_check.execute_check("database")
    assert result.status == HealthStatus.HEALTHY
    assert "latency_ms" in result.details

@pytest.mark.asyncio
async def test_check_timeout(health_check):
    async def slow_check():
        await asyncio.sleep(3)  # Longer than timeout
        return CheckResult(
            name="slow",
            status=HealthStatus.HEALTHY
        )
    
    await health_check.register_check("slow", slow_check)
    
    with pytest.raises(HealthError) as exc_info:
        await health_check.execute_check("slow")
    
    assert "timeout" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_check_failure_handling(health_check):
    failure_count = 0
    
    async def failing_check():
        nonlocal failure_count
        failure_count += 1
        if failure_count <= 3:  # Fail first three attempts
            raise Exception("Check failed")
        return CheckResult(
            name="failing",
            status=HealthStatus.HEALTHY
        )
    
    await health_check.register_check("failing", failing_check)
    
    # Should retry and eventually succeed
    result = await health_check.execute_check_with_retry("failing")
    assert result.status == HealthStatus.HEALTHY
    assert failure_count == 4

@pytest.mark.asyncio
async def test_check_status_tracking(health_check, sample_checks):
    await health_check.register_check("api", sample_checks["api"])
    
    # Execute check multiple times
    for _ in range(5):
        await health_check.execute_check("api")
    
    status = await health_check.get_check_status("api")
    assert status.total_executions == 5
    assert status.success_count == 5
    assert status.last_success is not None

@pytest.mark.asyncio
async def test_check_dependencies(health_check):
    checks_executed = []
    
    async def dependency_check():
        checks_executed.append("dependency")
        return CheckResult(
            name="dependency",
            status=HealthStatus.HEALTHY
        )
    
    async def dependent_check():
        checks_executed.append("dependent")
        return CheckResult(
            name="dependent",
            status=HealthStatus.HEALTHY
        )
    
    await health_check.register_check("dependency", dependency_check)
    await health_check.register_check(
        "dependent",
        dependent_check,
        dependencies=["dependency"]
    )
    
    await health_check.execute_check("dependent")
    assert checks_executed == ["dependency", "dependent"]

@pytest.mark.asyncio
async def test_check_aggregation(health_check, sample_checks):
    for name, check in sample_checks.items():
        await health_check.register_check(name, check)
    
    # Execute all checks
    results = await health_check.execute_all_checks()
    
    assert len(results) == len(sample_checks)
    assert all(r.status == HealthStatus.HEALTHY for r in results)

@pytest.mark.asyncio
async def test_check_metrics(health_check):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        async def check():
            return CheckResult(
                name="test",
                status=HealthStatus.HEALTHY,
                details={"duration_ms": 100}
            )
        
        await health_check.register_check("test", check)
        await health_check.execute_check("test")
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_gauge.assert_called()

@pytest.mark.asyncio
async def test_check_persistence(health_check):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        await health_check.save_state()
        mock_file.write.assert_called_once()
        
        await health_check.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_concurrent_check_execution(health_check, sample_checks):
    for name, check in sample_checks.items():
        await health_check.register_check(name, check)
    
    # Execute checks concurrently
    results = await asyncio.gather(*[
        health_check.execute_check(name)
        for name in sample_checks
    ])
    
    assert len(results) == len(sample_checks)
    assert all(r.status == HealthStatus.HEALTHY for r in results)

@pytest.mark.asyncio
async def test_check_history(health_check):
    async def check():
        return CheckResult(
            name="test",
            status=HealthStatus.HEALTHY
        )
    
    await health_check.register_check("test", check)
    
    # Execute check multiple times
    for _ in range(5):
        await health_check.execute_check("test")
    
    history = await health_check.get_check_history("test")
    assert len(history) == 5
    assert all(r.status == HealthStatus.HEALTHY for r in history)

@pytest.mark.asyncio
async def test_check_scheduling(health_check):
    check_executions = 0
    
    async def scheduled_check():
        nonlocal check_executions
        check_executions += 1
        return CheckResult(
            name="scheduled",
            status=HealthStatus.HEALTHY
        )
    
    await health_check.register_check(
        "scheduled",
        scheduled_check,
        interval=0.1  # 100ms
    )
    
    # Start scheduled execution
    await health_check.start_scheduled_checks()
    
    # Wait for multiple executions
    await asyncio.sleep(0.5)
    
    # Stop scheduled execution
    await health_check.stop_scheduled_checks()
    
    assert check_executions > 1

@pytest.mark.asyncio
async def test_check_cleanup(health_check):
    async def check():
        return CheckResult(
            name="test",
            status=HealthStatus.HEALTHY
        )
    
    await health_check.register_check("test", check)
    
    # Execute check and mark for cleanup
    await health_check.execute_check("test")
    await health_check.mark_for_cleanup("test")
    
    # Run cleanup
    await health_check.cleanup()
    
    assert "test" not in health_check.checks 