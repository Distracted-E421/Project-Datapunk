import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.health import (
    HealthChecker,
    HealthCheck,
    HealthStatus,
    HealthCheckResult,
    HealthCheckConfig
)

@pytest.fixture
def health_config():
    return HealthCheckConfig(
        check_interval=1,
        timeout_seconds=5,
        failure_threshold=3
    )

@pytest.fixture
def health_checker(health_config):
    return HealthChecker(config=health_config)

@pytest.fixture
def sample_check():
    async def check_func():
        return True
    
    return HealthCheck(
        name="test_check",
        check_func=check_func,
        interval_seconds=1
    )

@pytest.mark.asyncio
async def test_health_check_execution(health_checker, sample_check):
    health_checker.register_check(sample_check)
    result = await health_checker.execute_check(sample_check)
    
    assert result.status == HealthStatus.HEALTHY
    assert result.check_name == "test_check"
    assert result.timestamp is not None

@pytest.mark.asyncio
async def test_health_check_timeout():
    async def slow_check():
        await asyncio.sleep(0.2)
        return True
    
    checker = HealthChecker(
        HealthCheckConfig(timeout_seconds=0.1)
    )
    check = HealthCheck("slow_check", slow_check)
    
    result = await checker.execute_check(check)
    assert result.status == HealthStatus.UNHEALTHY
    assert "timeout" in result.message.lower()

@pytest.mark.asyncio
async def test_multiple_health_checks(health_checker):
    checks = [
        HealthCheck("check1", AsyncMock(return_value=True)),
        HealthCheck("check2", AsyncMock(return_value=True)),
        HealthCheck("check3", AsyncMock(return_value=False))
    ]
    
    for check in checks:
        health_checker.register_check(check)
    
    results = await health_checker.check_all()
    assert len(results) == 3
    assert sum(1 for r in results if r.status == HealthStatus.HEALTHY) == 2
    assert sum(1 for r in results if r.status == HealthStatus.UNHEALTHY) == 1

@pytest.mark.asyncio
async def test_health_check_history(health_checker, sample_check):
    health_checker.register_check(sample_check)
    
    # Execute check multiple times
    for _ in range(3):
        await health_checker.execute_check(sample_check)
        await asyncio.sleep(0.1)
    
    history = health_checker.get_check_history(sample_check.name)
    assert len(history) == 3
    assert all(r.status == HealthStatus.HEALTHY for r in history)

@pytest.mark.asyncio
async def test_health_status_transitions(health_checker):
    status_changes = []
    
    async def failing_check():
        return False
    
    check = HealthCheck("failing", failing_check)
    health_checker.register_check(check)
    
    # Monitor status changes
    health_checker.on_status_change(lambda old, new: status_changes.append((old, new)))
    
    # Execute check multiple times
    for _ in range(health_checker.config.failure_threshold + 1):
        await health_checker.execute_check(check)
    
    assert len(status_changes) > 0
    assert status_changes[-1][1] == HealthStatus.UNHEALTHY

@pytest.mark.asyncio
async def test_dependent_health_checks(health_checker):
    dependency_check = HealthCheck(
        "dependency",
        AsyncMock(return_value=True)
    )
    
    async def dependent_check():
        if health_checker.get_check_status("dependency") == HealthStatus.HEALTHY:
            return True
        return False
    
    dependent = HealthCheck(
        "dependent",
        dependent_check,
        dependencies=["dependency"]
    )
    
    health_checker.register_check(dependency_check)
    health_checker.register_check(dependent)
    
    results = await health_checker.check_all()
    assert all(r.status == HealthStatus.HEALTHY for r in results)

@pytest.mark.asyncio
async def test_health_check_metrics(health_checker, sample_check):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        health_checker.register_check(sample_check)
        await health_checker.execute_check(sample_check)
        
        mock_collector.return_value.record_gauge.assert_called()
        mock_collector.return_value.record_histogram.assert_called()

@pytest.mark.asyncio
async def test_health_check_recovery(health_checker):
    failing = True
    
    async def intermittent_check():
        nonlocal failing
        failing = not failing
        return not failing
    
    check = HealthCheck("intermittent", intermittent_check)
    health_checker.register_check(check)
    
    # Execute check multiple times
    results = []
    for _ in range(4):
        result = await health_checker.execute_check(check)
        results.append(result.status)
    
    assert HealthStatus.HEALTHY in results
    assert HealthStatus.UNHEALTHY in results

@pytest.mark.asyncio
async def test_health_check_custom_validator(health_checker):
    async def check_with_data():
        return {"cpu": 80, "memory": 70}
    
    def validate_metrics(data):
        return all(v < 90 for v in data.values())
    
    check = HealthCheck(
        "metrics",
        check_with_data,
        validator=validate_metrics
    )
    
    health_checker.register_check(check)
    result = await health_checker.execute_check(check)
    assert result.status == HealthStatus.HEALTHY

@pytest.mark.asyncio
async def test_health_check_cleanup(health_checker):
    check = HealthCheck(
        "test",
        AsyncMock(return_value=True),
        cleanup=AsyncMock()
    )
    
    health_checker.register_check(check)
    await health_checker.cleanup()
    
    check.cleanup.assert_called_once()

@pytest.mark.asyncio
async def test_health_check_rate_limiting(health_checker, sample_check):
    health_checker.register_check(sample_check)
    
    # Execute check rapidly
    for _ in range(5):
        await health_checker.execute_check(sample_check)
    
    # Check should respect minimum interval
    history = health_checker.get_check_history(sample_check.name)
    for i in range(1, len(history)):
        time_diff = history[i].timestamp - history[i-1].timestamp
        assert time_diff.total_seconds() >= sample_check.interval_seconds