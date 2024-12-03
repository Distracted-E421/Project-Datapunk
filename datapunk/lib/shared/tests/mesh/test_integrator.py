import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh import (
    MeshIntegrator,
    IntegratorConfig,
    ServiceEvent,
    IntegrationError,
    ServiceState
)

@pytest.fixture
def integrator_config():
    return IntegratorConfig(
        service_name="test-service",
        integration_timeout=5.0,
        retry_delay=0.1,
        max_retries=3,
        event_buffer_size=100
    )

@pytest.fixture
def mesh_integrator(integrator_config):
    return MeshIntegrator(config=integrator_config)

@pytest.mark.asyncio
async def test_integrator_initialization(mesh_integrator, integrator_config):
    assert mesh_integrator.config == integrator_config
    assert mesh_integrator.service_name == "test-service"
    assert not mesh_integrator.is_integrated
    assert len(mesh_integrator.event_handlers) == 0

@pytest.mark.asyncio
async def test_service_integration():
    with patch('datapunk_shared.mesh.ServiceDiscovery') as mock_discovery:
        integrator = MeshIntegrator(IntegratorConfig(
            service_name="test-service"
        ))
        
        mock_discovery.register_service.return_value = True
        
        await integrator.integrate()
        
        assert integrator.is_integrated
        mock_discovery.register_service.assert_called_once()

@pytest.mark.asyncio
async def test_event_handling(mesh_integrator):
    handled_events = []
    
    async def event_handler(event):
        handled_events.append(event)
    
    # Register handler
    await mesh_integrator.register_event_handler(
        event_type="test-event",
        handler=event_handler
    )
    
    # Trigger event
    event = ServiceEvent(
        type="test-event",
        service="test-service",
        data={"message": "test"}
    )
    await mesh_integrator.handle_event(event)
    
    assert len(handled_events) == 1
    assert handled_events[0].type == "test-event"

@pytest.mark.asyncio
async def test_integration_retry():
    with patch('datapunk_shared.mesh.ServiceDiscovery') as mock_discovery:
        integrator = MeshIntegrator(IntegratorConfig(
            service_name="test-service",
            max_retries=2
        ))
        
        # Mock integration failure then success
        mock_discovery.register_service.side_effect = [
            Exception("Integration failed"),
            Exception("Integration failed"),
            True
        ]
        
        await integrator.integrate()
        
        assert integrator.is_integrated
        assert mock_discovery.register_service.call_count == 3

@pytest.mark.asyncio
async def test_event_buffering(mesh_integrator):
    events = []
    
    async def delayed_handler(event):
        await asyncio.sleep(0.1)
        events.append(event)
    
    await mesh_integrator.register_event_handler(
        event_type="test-event",
        handler=delayed_handler
    )
    
    # Send multiple events rapidly
    test_events = [
        ServiceEvent(
            type="test-event",
            service="test-service",
            data={"id": i}
        )
        for i in range(5)
    ]
    
    for event in test_events:
        await mesh_integrator.handle_event(event)
    
    await asyncio.sleep(0.3)
    assert len(events) == 5

@pytest.mark.asyncio
async def test_service_state_management(mesh_integrator):
    state_changes = []
    
    async def state_handler(old_state, new_state):
        state_changes.append((old_state, new_state))
    
    mesh_integrator.on_state_change(state_handler)
    
    await mesh_integrator.set_state(ServiceState.STARTING)
    await mesh_integrator.set_state(ServiceState.RUNNING)
    await mesh_integrator.set_state(ServiceState.STOPPING)
    
    assert len(state_changes) == 3
    assert state_changes[-1][1] == ServiceState.STOPPING

@pytest.mark.asyncio
async def test_error_handling(mesh_integrator):
    error_events = []
    
    async def error_handler(error):
        error_events.append(error)
    
    mesh_integrator.on_error(error_handler)
    
    # Simulate error in event handling
    async def failing_handler(event):
        raise Exception("Handler failed")
    
    await mesh_integrator.register_event_handler(
        event_type="test-event",
        handler=failing_handler
    )
    
    event = ServiceEvent(
        type="test-event",
        service="test-service",
        data={"message": "test"}
    )
    
    await mesh_integrator.handle_event(event)
    assert len(error_events) == 1
    assert isinstance(error_events[0], Exception)

@pytest.mark.asyncio
async def test_metrics_collection(mesh_integrator):
    with patch('datapunk_shared.metrics.MetricsCollector') as mock_collector:
        # Integrate service
        await mesh_integrator.integrate()
        
        # Handle some events
        for i in range(3):
            event = ServiceEvent(
                type="test-event",
                service="test-service",
                data={"id": i}
            )
            await mesh_integrator.handle_event(event)
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_histogram.assert_called()

@pytest.mark.asyncio
async def test_concurrent_event_handling(mesh_integrator):
    processed_events = []
    
    async def slow_handler(event):
        await asyncio.sleep(0.1)
        processed_events.append(event)
    
    await mesh_integrator.register_event_handler(
        event_type="test-event",
        handler=slow_handler,
        concurrent=True
    )
    
    # Send events concurrently
    events = [
        ServiceEvent(
            type="test-event",
            service="test-service",
            data={"id": i}
        )
        for i in range(3)
    ]
    
    start_time = datetime.utcnow()
    
    await asyncio.gather(*[
        mesh_integrator.handle_event(event)
        for event in events
    ])
    
    await asyncio.sleep(0.2)  # Wait for processing
    
    processing_time = (datetime.utcnow() - start_time).total_seconds()
    assert len(processed_events) == 3
    assert processing_time < 0.3  # Should be faster than sequential processing

@pytest.mark.asyncio
async def test_integration_cleanup(mesh_integrator):
    cleanup_called = False
    
    async def cleanup_handler():
        nonlocal cleanup_called
        cleanup_called = True
    
    mesh_integrator.on_cleanup(cleanup_handler)
    
    await mesh_integrator.integrate()
    await mesh_integrator.cleanup()
    
    assert cleanup_called
    assert not mesh_integrator.is_integrated

@pytest.mark.asyncio
async def test_event_filtering(mesh_integrator):
    filtered_events = []
    
    def event_filter(event):
        return int(event.data["id"]) % 2 == 0
    
    async def event_handler(event):
        filtered_events.append(event)
    
    await mesh_integrator.register_event_handler(
        event_type="test-event",
        handler=event_handler,
        filter_func=event_filter
    )
    
    # Send events with different IDs
    for i in range(5):
        event = ServiceEvent(
            type="test-event",
            service="test-service",
            data={"id": i}
        )
        await mesh_integrator.handle_event(event)
    
    assert len(filtered_events) == 3  # Only events with even IDs

@pytest.mark.asyncio
async def test_event_prioritization(mesh_integrator):
    processed_events = []
    
    async def event_handler(event):
        processed_events.append(event)
    
    await mesh_integrator.register_event_handler(
        event_type="test-event",
        handler=event_handler
    )
    
    # Send events with different priorities
    events = [
        ServiceEvent(
            type="test-event",
            service="test-service",
            data={"id": i},
            priority=i
        )
        for i in range(3)
    ]
    
    # Send in reverse order
    for event in reversed(events):
        await mesh_integrator.handle_event(event)
    
    assert len(processed_events) == 3
    assert [event.priority for event in processed_events] == [2, 1, 0] 