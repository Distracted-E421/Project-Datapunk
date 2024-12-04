import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk.lib.service import (
    ServiceManager,
    ServiceConfig,
    ServiceState,
    ServiceError,
    ServiceLifecycle
)

@pytest.fixture
def service_config():
    return ServiceConfig(
        name="test_service",
        version="1.0.0",
        dependencies=[
            {
                "name": "database",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432
            },
            {
                "name": "cache",
                "type": "redis",
                "host": "localhost",
                "port": 6379
            }
        ],
        health_check={
            "enabled": True,
            "interval": 30,
            "timeout": 5
        },
        metrics={
            "enabled": True,
            "port": 9090
        },
        lifecycle_hooks={
            "pre_start": ["check_config", "init_connections"],
            "post_start": ["register_service"],
            "pre_stop": ["deregister_service"],
            "post_stop": ["cleanup_connections"]
        }
    )

@pytest.fixture
async def service_manager(service_config):
    manager = ServiceManager(service_config)
    await manager.initialize()
    return manager

@pytest.mark.asyncio
async def test_manager_initialization(service_manager, service_config):
    """Test service manager initialization"""
    assert service_manager.config == service_config
    assert service_manager.is_initialized
    assert service_manager.state == ServiceState.INITIALIZED

@pytest.mark.asyncio
async def test_service_startup(service_manager):
    """Test service startup sequence"""
    # Mock dependency checks
    async def mock_check_dependency(dep):
        return True
    
    service_manager.add_dependency_check(mock_check_dependency)
    
    # Start service
    await service_manager.start()
    
    assert service_manager.state == ServiceState.RUNNING
    assert service_manager.start_time is not None

@pytest.mark.asyncio
async def test_service_shutdown(service_manager):
    """Test service shutdown sequence"""
    # Start service first
    await service_manager.start()
    
    # Stop service
    await service_manager.stop()
    
    assert service_manager.state == ServiceState.STOPPED
    assert service_manager.stop_time is not None

@pytest.mark.asyncio
async def test_dependency_management(service_manager):
    """Test dependency management"""
    # Mock dependency checks
    dependency_checks = {
        "database": True,
        "cache": False
    }
    
    async def mock_check_dependency(dep):
        return dependency_checks.get(dep["name"], False)
    
    service_manager.add_dependency_check(mock_check_dependency)
    
    # Try to start service with failed dependency
    with pytest.raises(ServiceError):
        await service_manager.start()
    
    assert service_manager.state == ServiceState.FAILED

@pytest.mark.asyncio
async def test_lifecycle_hooks(service_manager):
    """Test lifecycle hooks execution"""
    hook_calls = []
    
    async def mock_hook(name):
        hook_calls.append(name)
        return True
    
    service_manager.add_lifecycle_hook(mock_hook)
    
    # Start and stop service
    await service_manager.start()
    await service_manager.stop()
    
    # Verify hook execution order
    expected_hooks = [
        "check_config",
        "init_connections",
        "register_service",
        "deregister_service",
        "cleanup_connections"
    ]
    
    assert hook_calls == expected_hooks

@pytest.mark.asyncio
async def test_health_checks(service_manager):
    """Test service health checks"""
    health_checks = []
    
    async def mock_health_check():
        health_checks.append(datetime.now())
        return True
    
    service_manager.add_health_check(mock_health_check)
    
    # Start service and wait for health checks
    await service_manager.start()
    await asyncio.sleep(0.1)  # Allow health check to run
    
    assert len(health_checks) > 0

@pytest.mark.asyncio
async def test_metrics_collection(service_manager):
    """Test service metrics collection"""
    metrics = []
    
    def mock_metric_collector(metric):
        metrics.append(metric)
    
    service_manager.set_metrics_collector(mock_metric_collector)
    
    # Start service and generate some metrics
    await service_manager.start()
    await service_manager.record_metric("requests", 1)
    await service_manager.record_metric("latency", 100)
    
    assert len(metrics) == 2
    assert any(m["name"] == "requests" for m in metrics)
    assert any(m["name"] == "latency" for m in metrics)

@pytest.mark.asyncio
async def test_service_recovery(service_manager):
    """Test service recovery mechanism"""
    failure_count = 0
    
    async def mock_health_check():
        nonlocal failure_count
        failure_count += 1
        if failure_count <= 2:
            return False
        return True
    
    service_manager.add_health_check(mock_health_check)
    service_manager.config.recovery_attempts = 3
    
    # Start service
    await service_manager.start()
    
    # Simulate recovery
    await service_manager.handle_failure()
    
    assert service_manager.state == ServiceState.RUNNING
    assert service_manager.recovery_attempts == 2

@pytest.mark.asyncio
async def test_service_events(service_manager):
    """Test service event handling"""
    events = []
    
    def event_handler(event):
        events.append(event)
    
    service_manager.add_event_handler(event_handler)
    
    # Generate service events
    await service_manager.start()
    await service_manager.emit_event("test_event", {"data": "test"})
    await service_manager.stop()
    
    assert len(events) > 0
    assert any(e["type"] == "test_event" for e in events)

@pytest.mark.asyncio
async def test_service_state_transitions(service_manager):
    """Test service state transitions"""
    states = []
    
    def state_change_handler(old_state, new_state):
        states.append((old_state, new_state))
    
    service_manager.add_state_change_handler(state_change_handler)
    
    # Trigger state transitions
    await service_manager.start()
    await service_manager.pause()
    await service_manager.resume()
    await service_manager.stop()
    
    expected_transitions = [
        (ServiceState.INITIALIZED, ServiceState.STARTING),
        (ServiceState.STARTING, ServiceState.RUNNING),
        (ServiceState.RUNNING, ServiceState.PAUSED),
        (ServiceState.PAUSED, ServiceState.RUNNING),
        (ServiceState.RUNNING, ServiceState.STOPPING),
        (ServiceState.STOPPING, ServiceState.STOPPED)
    ]
    
    assert states == expected_transitions

@pytest.mark.asyncio
async def test_error_handling(service_manager):
    """Test error handling"""
    # Test with invalid state transition
    with pytest.raises(ServiceError):
        await service_manager.stop()  # Can't stop before starting
    
    # Test with invalid configuration
    with pytest.raises(ServiceError):
        service_manager.config.name = ""  # Invalid name
        await service_manager.validate_config()

@pytest.mark.asyncio
async def test_service_discovery(service_manager):
    """Test service discovery integration"""
    discovered_services = []
    
    async def mock_discovery_register(service_info):
        discovered_services.append(service_info)
    
    service_manager.set_discovery_handler(mock_discovery_register)
    
    # Start service with discovery
    await service_manager.start()
    
    assert len(discovered_services) == 1
    assert discovered_services[0]["name"] == service_manager.config.name
    assert discovered_services[0]["version"] == service_manager.config.version

@pytest.mark.asyncio
async def test_graceful_shutdown(service_manager):
    """Test graceful shutdown handling"""
    shutdown_steps = []
    
    async def mock_shutdown_step(step):
        shutdown_steps.append(step)
        await asyncio.sleep(0.1)  # Simulate work
    
    service_manager.add_shutdown_handler(mock_shutdown_step)
    
    # Start and then gracefully stop
    await service_manager.start()
    await service_manager.graceful_shutdown(timeout=1.0)
    
    assert service_manager.state == ServiceState.STOPPED
    assert len(shutdown_steps) > 0

@pytest.mark.asyncio
async def test_service_monitoring(service_manager):
    """Test service monitoring"""
    monitor_data = []
    
    def mock_monitor(data):
        monitor_data.append(data)
    
    service_manager.add_monitor(mock_monitor)
    
    # Start service and generate some monitoring data
    await service_manager.start()
    await service_manager.update_status("healthy")
    await service_manager.record_metric("cpu_usage", 50)
    
    assert len(monitor_data) > 0
    assert any("status" in d for d in monitor_data)
    assert any("metrics" in d for d in monitor_data) 