import pytest
import asyncio
from datetime import datetime
from datapunk.lib.monitoring.health_check import (
    HealthStatus, HealthCheckResult, HealthCheck, HealthCheckManager
)

@pytest.fixture
def health_check_result():
    return HealthCheckResult(
        status=HealthStatus.HEALTHY,
        message="Test check passed",
        timestamp=datetime.now()
    )

@pytest.fixture
def mock_check_func(health_check_result):
    async def _check():
        return health_check_result
    return _check

@pytest.fixture
def health_check(mock_check_func):
    return HealthCheck(
        name="test_check",
        check_func=mock_check_func,
        interval_seconds=1,
        timeout_seconds=5
    )

@pytest.fixture
def health_check_manager():
    return HealthCheckManager()

@pytest.mark.asyncio
async def test_health_check_execution(health_check):
    result = await health_check.execute()
    assert result.status == HealthStatus.HEALTHY
    assert result.message == "Test check passed"
    assert isinstance(result.timestamp, datetime)

@pytest.mark.asyncio
async def test_health_check_timeout():
    async def slow_check():
        await asyncio.sleep(2)
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message="Should not reach here",
            timestamp=datetime.now()
        )
    
    check = HealthCheck(
        name="slow_check",
        check_func=slow_check,
        timeout_seconds=1
    )
    
    result = await check.execute()
    assert result.status == HealthStatus.UNHEALTHY
    assert "timed out" in result.message.lower()

@pytest.mark.asyncio
async def test_health_check_error():
    async def failing_check():
        raise ValueError("Test error")
    
    check = HealthCheck(
        name="failing_check",
        check_func=failing_check
    )
    
    result = await check.execute()
    assert result.status == HealthStatus.UNHEALTHY
    assert "failed" in result.message.lower()
    assert result.details["type"] == "ValueError"
    assert result.details["error"] == "Test error"

@pytest.mark.asyncio
async def test_health_check_manager_registration(health_check_manager, health_check):
    health_check_manager.register_check(health_check)
    assert "test_check" in health_check_manager.checks
    assert health_check_manager.checks["test_check"] == health_check

def test_health_check_manager_duplicate_registration(health_check_manager, health_check):
    health_check_manager.register_check(health_check)
    with pytest.raises(ValueError, match="already registered"):
        health_check_manager.register_check(health_check)

@pytest.mark.asyncio
async def test_health_check_manager_dependency_validation(health_check_manager):
    check_with_deps = HealthCheck(
        name="dependent_check",
        check_func=lambda: None,
        dependencies=["nonexistent_check"]
    )
    
    with pytest.raises(ValueError, match="Dependency.*not found"):
        health_check_manager.register_check(check_with_deps)

@pytest.mark.asyncio
async def test_health_check_manager_start_stop(health_check_manager, health_check):
    health_check_manager.register_check(health_check)
    
    await health_check_manager.start()
    assert health_check_manager._running
    assert len(health_check_manager._check_tasks) == 1
    
    await health_check_manager.stop()
    assert not health_check_manager._running
    assert len(health_check_manager._check_tasks) == 0

@pytest.mark.asyncio
async def test_health_check_manager_unregister(health_check_manager, health_check):
    health_check_manager.register_check(health_check)
    await health_check_manager.start()
    
    health_check_manager.unregister_check("test_check")
    assert "test_check" not in health_check_manager.checks
    assert "test_check" not in health_check_manager._check_tasks

@pytest.mark.asyncio
async def test_health_check_manager_status_methods(health_check_manager, health_check):
    health_check_manager.register_check(health_check)
    await health_check_manager.start()
    
    # Wait for first check to complete
    await asyncio.sleep(1.1)
    
    # Test get_status
    statuses = health_check_manager.get_status()
    assert "test_check" in statuses
    assert statuses["test_check"].status == HealthStatus.HEALTHY
    
    # Test get_check_status
    status = health_check_manager.get_check_status("test_check")
    assert status.status == HealthStatus.HEALTHY
    
    # Test is_healthy
    assert health_check_manager.is_healthy()
    
    # Test get_unhealthy_checks
    unhealthy = health_check_manager.get_unhealthy_checks()
    assert len(unhealthy) == 0

@pytest.mark.asyncio
async def test_health_check_manager_priority_ordering(health_check_manager):
    execution_order = []
    
    async def check_func(name):
        execution_order.append(name)
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            message=f"{name} executed",
            timestamp=datetime.now()
        )
    
    check1 = HealthCheck("check1", lambda: check_func("check1"), priority=2)
    check2 = HealthCheck("check2", lambda: check_func("check2"), priority=1)
    check3 = HealthCheck("check3", lambda: check_func("check3"), priority=0)
    
    health_check_manager.register_check(check1)
    health_check_manager.register_check(check2)
    health_check_manager.register_check(check3)
    
    await health_check_manager.start()
    await asyncio.sleep(1.1)  # Wait for first round of checks
    
    assert execution_order[:3] == ["check3", "check2", "check1"]
    await health_check_manager.stop() 