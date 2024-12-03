import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.circuit_breaker import (
    CircuitBreakerManager,
    ManagerConfig,
    CircuitBreaker,
    CircuitState,
    CircuitConfig,
    CircuitEvent
)

@pytest.fixture
def manager_config():
    return ManagerConfig(
        sync_interval=30,  # 30 seconds
        cleanup_interval=300,  # 5 minutes
        max_circuits=100,
        enable_metrics=True
    )

@pytest.fixture
def circuit_manager(manager_config):
    return CircuitBreakerManager(config=manager_config)

@pytest.fixture
def sample_circuit_configs():
    return [
        CircuitConfig(
            circuit_id="service1",
            failure_threshold=5,
            success_threshold=3,
            timeout_seconds=60,
            half_open_max_calls=2
        ),
        CircuitConfig(
            circuit_id="service2",
            failure_threshold=3,
            success_threshold=2,
            timeout_seconds=30,
            half_open_max_calls=1
        )
    ]

@pytest.mark.asyncio
async def test_manager_initialization(circuit_manager, manager_config):
    assert circuit_manager.config == manager_config
    assert circuit_manager.is_initialized
    assert len(circuit_manager.circuits) == 0

@pytest.mark.asyncio
async def test_circuit_creation(circuit_manager, sample_circuit_configs):
    for config in sample_circuit_configs:
        circuit = await circuit_manager.create_circuit(config)
        assert isinstance(circuit, CircuitBreaker)
        assert circuit.config == config

@pytest.mark.asyncio
async def test_circuit_registration(circuit_manager, sample_circuit_configs):
    # Create and register circuits
    for config in sample_circuit_configs:
        await circuit_manager.register_circuit(config)
    
    assert len(circuit_manager.circuits) == len(sample_circuit_configs)
    assert all(c.circuit_id in circuit_manager.circuits 
              for c in sample_circuit_configs)

@pytest.mark.asyncio
async def test_circuit_state_management(circuit_manager):
    config = CircuitConfig(
        circuit_id="test_circuit",
        failure_threshold=2,
        success_threshold=1,
        timeout_seconds=30,
        half_open_max_calls=1
    )
    
    circuit = await circuit_manager.create_circuit(config)
    
    # Trigger failures to open circuit
    for _ in range(3):
        await circuit.record_failure()
    
    assert circuit.state == CircuitState.OPEN
    
    # Wait for timeout and transition to half-open
    await asyncio.sleep(0.1)  # Simulate time passing
    with patch.object(circuit, '_get_elapsed_time') as mock_time:
        mock_time.return_value = timedelta(seconds=31)
        await circuit_manager.check_circuits()
        assert circuit.state == CircuitState.HALF_OPEN

@pytest.mark.asyncio
async def test_circuit_events(circuit_manager, sample_circuit_configs):
    events = []
    
    def event_handler(event: CircuitEvent):
        events.append(event)
    
    circuit_manager.on_circuit_event(event_handler)
    
    # Create circuit and trigger state change
    config = sample_circuit_configs[0]
    circuit = await circuit_manager.create_circuit(config)
    
    for _ in range(6):  # Exceed failure threshold
        await circuit.record_failure()
    
    assert len(events) > 0
    assert events[0].circuit_id == config.circuit_id
    assert events[0].event_type == "state_changed"

@pytest.mark.asyncio
async def test_circuit_cleanup(circuit_manager):
    # Create circuit with short timeout
    config = CircuitConfig(
        circuit_id="temp_circuit",
        failure_threshold=5,
        success_threshold=3,
        timeout_seconds=1,
        half_open_max_calls=2
    )
    
    await circuit_manager.register_circuit(config)
    
    # Mark circuit for cleanup
    circuit_manager.mark_for_cleanup("temp_circuit")
    
    # Run cleanup
    await circuit_manager.cleanup()
    
    assert "temp_circuit" not in circuit_manager.circuits

@pytest.mark.asyncio
async def test_concurrent_circuit_operations(circuit_manager):
    # Generate multiple circuit configs
    configs = [
        CircuitConfig(
            circuit_id=f"circuit{i}",
            failure_threshold=5,
            success_threshold=3,
            timeout_seconds=60,
            half_open_max_calls=2
        )
        for i in range(50)
    ]
    
    # Create circuits concurrently
    await asyncio.gather(*[
        circuit_manager.create_circuit(config)
        for config in configs
    ])
    
    assert len(circuit_manager.circuits) == 50

@pytest.mark.asyncio
async def test_circuit_metrics_collection(circuit_manager):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        config = CircuitConfig(
            circuit_id="metrics_circuit",
            failure_threshold=5,
            success_threshold=3,
            timeout_seconds=60,
            half_open_max_calls=2
        )
        
        circuit = await circuit_manager.create_circuit(config)
        await circuit.record_failure()
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_gauge.assert_called()

@pytest.mark.asyncio
async def test_circuit_persistence(circuit_manager):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        await circuit_manager.save_state()
        mock_file.write.assert_called_once()
        
        await circuit_manager.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_circuit_coordination(circuit_manager):
    # Create multiple circuits for the same service
    configs = [
        CircuitConfig(
            circuit_id=f"service1_instance{i}",
            failure_threshold=5,
            success_threshold=3,
            timeout_seconds=60,
            half_open_max_calls=2
        )
        for i in range(3)
    ]
    
    circuits = []
    for config in configs:
        circuit = await circuit_manager.create_circuit(config)
        circuits.append(circuit)
    
    # Trigger failures in one circuit
    for _ in range(6):
        await circuits[0].record_failure()
    
    # Check if other circuits are notified
    assert all(c.state == CircuitState.OPEN for c in circuits)

@pytest.mark.asyncio
async def test_circuit_recovery(circuit_manager):
    config = CircuitConfig(
        circuit_id="recovery_circuit",
        failure_threshold=2,
        success_threshold=2,
        timeout_seconds=1,
        half_open_max_calls=2
    )
    
    circuit = await circuit_manager.create_circuit(config)
    
    # Open circuit
    for _ in range(3):
        await circuit.record_failure()
    
    assert circuit.state == CircuitState.OPEN
    
    # Wait for timeout
    await asyncio.sleep(1.1)
    
    # Simulate successful calls
    await circuit.record_success()
    await circuit.record_success()
    
    assert circuit.state == CircuitState.CLOSED

@pytest.mark.asyncio
async def test_circuit_configuration_updates(circuit_manager):
    initial_config = CircuitConfig(
        circuit_id="update_circuit",
        failure_threshold=5,
        success_threshold=3,
        timeout_seconds=60,
        half_open_max_calls=2
    )
    
    circuit = await circuit_manager.create_circuit(initial_config)
    
    # Update configuration
    updated_config = CircuitConfig(
        circuit_id="update_circuit",
        failure_threshold=3,  # Lower threshold
        success_threshold=2,
        timeout_seconds=30,
        half_open_max_calls=1
    )
    
    await circuit_manager.update_circuit_config(updated_config)
    
    assert circuit.config.failure_threshold == 3
    assert circuit.config.timeout_seconds == 30

@pytest.mark.asyncio
async def test_circuit_metrics_aggregation(circuit_manager, sample_circuit_configs):
    # Create multiple circuits and record events
    circuits = []
    for config in sample_circuit_configs:
        circuit = await circuit_manager.create_circuit(config)
        circuits.append(circuit)
    
    # Record some failures and successes
    for circuit in circuits:
        await circuit.record_failure()
        await circuit.record_success()
    
    # Get aggregated metrics
    metrics = await circuit_manager.get_aggregated_metrics()
    
    assert "total_circuits" in metrics
    assert "open_circuits" in metrics
    assert "failure_rate" in metrics 