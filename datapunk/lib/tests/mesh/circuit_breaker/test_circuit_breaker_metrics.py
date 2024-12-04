import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.circuit_breaker import (
    CircuitBreakerMetrics,
    MetricsConfig,
    CircuitState,
    FailureEvent,
    StateTransition,
    CircuitStats
)

@pytest.fixture
def metrics_config():
    return MetricsConfig(
        collection_interval=60,  # 1 minute
        retention_period=3600,  # 1 hour
        failure_threshold=5,
        success_threshold=3
    )

@pytest.fixture
def circuit_metrics(metrics_config):
    return CircuitBreakerMetrics(config=metrics_config)

@pytest.fixture
def sample_failure_events():
    return [
        FailureEvent(
            circuit_id="service1",
            error_type="timeout",
            timestamp=datetime.utcnow(),
            duration_ms=500,
            context={"endpoint": "/api/data"}
        ),
        FailureEvent(
            circuit_id="service1",
            error_type="connection_error",
            timestamp=datetime.utcnow(),
            duration_ms=300,
            context={"endpoint": "/api/users"}
        )
    ]

@pytest.mark.asyncio
async def test_metrics_initialization(circuit_metrics, metrics_config):
    assert circuit_metrics.config == metrics_config
    assert circuit_metrics.is_initialized
    assert len(circuit_metrics.failure_events) == 0
    assert len(circuit_metrics.state_transitions) == 0

@pytest.mark.asyncio
async def test_failure_recording(circuit_metrics, sample_failure_events):
    for event in sample_failure_events:
        await circuit_metrics.record_failure(event)
    
    assert len(circuit_metrics.failure_events) == len(sample_failure_events)
    assert all(e.circuit_id == "service1" for e in circuit_metrics.failure_events)

@pytest.mark.asyncio
async def test_state_transition_tracking(circuit_metrics):
    # Record state transitions
    transitions = [
        StateTransition(
            circuit_id="service1",
            from_state=CircuitState.CLOSED,
            to_state=CircuitState.OPEN,
            timestamp=datetime.utcnow(),
            reason="failure_threshold_exceeded"
        ),
        StateTransition(
            circuit_id="service1",
            from_state=CircuitState.OPEN,
            to_state=CircuitState.HALF_OPEN,
            timestamp=datetime.utcnow() + timedelta(minutes=1),
            reason="retry_timeout_elapsed"
        )
    ]
    
    for transition in transitions:
        await circuit_metrics.record_state_transition(transition)
    
    assert len(circuit_metrics.state_transitions) == len(transitions)
    assert circuit_metrics.state_transitions[-1].to_state == CircuitState.HALF_OPEN

@pytest.mark.asyncio
async def test_failure_rate_calculation(circuit_metrics):
    # Record mix of successes and failures
    for _ in range(10):
        await circuit_metrics.record_failure(FailureEvent(
            circuit_id="service1",
            error_type="timeout",
            timestamp=datetime.utcnow(),
            duration_ms=500,
            context={}
        ))
    
    for _ in range(10):
        await circuit_metrics.record_success("service1")
    
    failure_rate = await circuit_metrics.calculate_failure_rate(
        circuit_id="service1",
        window_seconds=60
    )
    
    assert failure_rate == 0.5  # 50% failure rate

@pytest.mark.asyncio
async def test_circuit_stats(circuit_metrics, sample_failure_events):
    # Record failures and successes
    for event in sample_failure_events:
        await circuit_metrics.record_failure(event)
    
    await circuit_metrics.record_success("service1")
    
    stats = await circuit_metrics.get_circuit_stats("service1")
    assert isinstance(stats, CircuitStats)
    assert stats.total_failures == len(sample_failure_events)
    assert stats.total_successes == 1

@pytest.mark.asyncio
async def test_metrics_aggregation(circuit_metrics, sample_failure_events):
    # Record events with different timestamps
    now = datetime.utcnow()
    
    events = [
        FailureEvent(
            circuit_id="service1",
            error_type=e.error_type,
            timestamp=now - timedelta(minutes=i),
            duration_ms=e.duration_ms,
            context=e.context
        )
        for i, e in enumerate(sample_failure_events * 3)
    ]
    
    for event in events:
        await circuit_metrics.record_failure(event)
    
    # Aggregate metrics
    aggregated = await circuit_metrics.aggregate_metrics(
        start_time=now - timedelta(hours=1)
    )
    
    assert "total_failures" in aggregated
    assert "failure_types" in aggregated
    assert "avg_duration_ms" in aggregated

@pytest.mark.asyncio
async def test_error_pattern_detection(circuit_metrics):
    # Record failures with patterns
    error_types = ["timeout", "connection_error", "timeout"]
    
    for error_type in error_types:
        await circuit_metrics.record_failure(FailureEvent(
            circuit_id="service1",
            error_type=error_type,
            timestamp=datetime.utcnow(),
            duration_ms=500,
            context={}
        ))
    
    patterns = await circuit_metrics.detect_error_patterns("service1")
    assert len(patterns) > 0
    assert any(p.error_type == "timeout" for p in patterns)

@pytest.mark.asyncio
async def test_metrics_cleanup(circuit_metrics):
    # Add old failure events
    old_event = FailureEvent(
        circuit_id="service1",
        error_type="timeout",
        timestamp=datetime.utcnow() - timedelta(hours=2),
        duration_ms=500,
        context={}
    )
    
    await circuit_metrics.record_failure(old_event)
    
    # Run cleanup
    await circuit_metrics.cleanup_old_events()
    
    assert len(circuit_metrics.failure_events) == 0

@pytest.mark.asyncio
async def test_concurrent_recording(circuit_metrics):
    # Generate multiple events
    events = [
        FailureEvent(
            circuit_id="service1",
            error_type="timeout",
            timestamp=datetime.utcnow(),
            duration_ms=500,
            context={"request_id": str(i)}
        )
        for i in range(100)
    ]
    
    # Record events concurrently
    await asyncio.gather(*[
        circuit_metrics.record_failure(event)
        for event in events
    ])
    
    assert len(circuit_metrics.failure_events) == 100

@pytest.mark.asyncio
async def test_metrics_persistence(circuit_metrics):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        await circuit_metrics.save_state()
        mock_file.write.assert_called_once()
        
        await circuit_metrics.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_threshold_monitoring(circuit_metrics):
    alerts = []
    
    def alert_handler(circuit_id: str, message: str):
        alerts.append((circuit_id, message))
    
    circuit_metrics.on_threshold_exceeded(alert_handler)
    
    # Generate failures to exceed threshold
    for _ in range(6):  # Threshold is 5
        await circuit_metrics.record_failure(FailureEvent(
            circuit_id="service1",
            error_type="timeout",
            timestamp=datetime.utcnow(),
            duration_ms=500,
            context={}
        ))
    
    assert len(alerts) > 0
    assert alerts[0][0] == "service1"

@pytest.mark.asyncio
async def test_performance_tracking(circuit_metrics):
    # Record requests with different durations
    durations = [100, 200, 300, 400, 500]  # ms
    
    for duration in durations:
        await circuit_metrics.record_failure(FailureEvent(
            circuit_id="service1",
            error_type="timeout",
            timestamp=datetime.utcnow(),
            duration_ms=duration,
            context={}
        ))
    
    performance = await circuit_metrics.get_performance_metrics("service1")
    assert performance.avg_duration_ms == sum(durations) / len(durations)
    assert performance.max_duration_ms == max(durations)

@pytest.mark.asyncio
async def test_state_duration_tracking(circuit_metrics):
    # Record state transition
    transition = StateTransition(
        circuit_id="service1",
        from_state=CircuitState.CLOSED,
        to_state=CircuitState.OPEN,
        timestamp=datetime.utcnow() - timedelta(minutes=5),
        reason="failure_threshold_exceeded"
    )
    
    await circuit_metrics.record_state_transition(transition)
    
    durations = await circuit_metrics.get_state_durations("service1")
    assert CircuitState.OPEN in durations
    assert durations[CircuitState.OPEN].total_seconds() >= 300  # 5 minutes 