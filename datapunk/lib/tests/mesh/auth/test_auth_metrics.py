import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.auth import (
    AuthMetrics,
    MetricsConfig,
    AuthEvent,
    PerformanceMetrics,
    AuthStats
)

@pytest.fixture
def metrics_config():
    return MetricsConfig(
        collection_interval=60,  # 1 minute
        retention_period=86400,  # 1 day
        performance_thresholds={
            "auth_latency_ms": 100,
            "token_validation_ms": 50
        }
    )

@pytest.fixture
def auth_metrics(metrics_config):
    return AuthMetrics(config=metrics_config)

@pytest.fixture
def sample_auth_events():
    return [
        AuthEvent(
            event_type="login",
            user_id="user123",
            timestamp=datetime.utcnow(),
            success=True,
            latency_ms=45,
            details={"method": "password"}
        ),
        AuthEvent(
            event_type="token_validation",
            user_id="user456",
            timestamp=datetime.utcnow(),
            success=False,
            latency_ms=30,
            details={"reason": "expired"}
        )
    ]

@pytest.mark.asyncio
async def test_metrics_initialization(auth_metrics, metrics_config):
    assert auth_metrics.config == metrics_config
    assert auth_metrics.is_initialized
    assert len(auth_metrics.events) == 0

@pytest.mark.asyncio
async def test_event_recording(auth_metrics, sample_auth_events):
    for event in sample_auth_events:
        await auth_metrics.record_event(event)
    
    assert len(auth_metrics.events) == len(sample_auth_events)
    assert all(e.event_type in ["login", "token_validation"] 
              for e in auth_metrics.events)

@pytest.mark.asyncio
async def test_success_rate_calculation(auth_metrics):
    # Record mix of successful and failed events
    events = [
        AuthEvent(
            event_type="login",
            user_id=f"user{i}",
            timestamp=datetime.utcnow(),
            success=i % 2 == 0,  # Alternate success/failure
            latency_ms=50,
            details={}
        )
        for i in range(10)
    ]
    
    for event in events:
        await auth_metrics.record_event(event)
    
    success_rate = await auth_metrics.calculate_success_rate(
        event_type="login",
        window_minutes=5
    )
    
    assert success_rate == 0.5  # 50% success rate

@pytest.mark.asyncio
async def test_performance_metrics(auth_metrics, sample_auth_events):
    for event in sample_auth_events:
        await auth_metrics.record_event(event)
    
    performance = await auth_metrics.get_performance_metrics(
        start_time=datetime.utcnow() - timedelta(minutes=5)
    )
    
    assert isinstance(performance, PerformanceMetrics)
    assert "avg_latency_ms" in performance.metrics
    assert "p95_latency_ms" in performance.metrics
    assert "p99_latency_ms" in performance.metrics

@pytest.mark.asyncio
async def test_user_metrics(auth_metrics):
    # Record events for specific users
    user_id = "test_user"
    events = [
        AuthEvent(
            event_type="login",
            user_id=user_id,
            timestamp=datetime.utcnow(),
            success=True,
            latency_ms=50,
            details={}
        )
        for _ in range(5)
    ]
    
    for event in events:
        await auth_metrics.record_event(event)
    
    user_stats = await auth_metrics.get_user_stats(user_id)
    assert user_stats.login_count == 5
    assert user_stats.success_rate == 1.0

@pytest.mark.asyncio
async def test_concurrent_event_recording(auth_metrics):
    # Generate multiple events
    events = [
        AuthEvent(
            event_type="login",
            user_id=f"user{i}",
            timestamp=datetime.utcnow(),
            success=True,
            latency_ms=50,
            details={}
        )
        for i in range(100)
    ]
    
    # Record events concurrently
    await asyncio.gather(*[
        auth_metrics.record_event(event)
        for event in events
    ])
    
    assert len(auth_metrics.events) == 100

@pytest.mark.asyncio
async def test_metrics_aggregation(auth_metrics, sample_auth_events):
    # Record events with different timestamps
    now = datetime.utcnow()
    
    events = [
        AuthEvent(
            event_type=e.event_type,
            user_id=e.user_id,
            timestamp=now - timedelta(minutes=i),
            success=e.success,
            latency_ms=e.latency_ms,
            details=e.details
        )
        for i, e in enumerate(sample_auth_events * 3)
    ]
    
    for event in events:
        await auth_metrics.record_event(event)
    
    # Aggregate metrics
    aggregated = await auth_metrics.aggregate_metrics(
        start_time=now - timedelta(hours=1)
    )
    
    assert "total_events" in aggregated
    assert "success_rate" in aggregated
    assert "avg_latency" in aggregated

@pytest.mark.asyncio
async def test_metrics_export(auth_metrics, sample_auth_events):
    for event in sample_auth_events:
        await auth_metrics.record_event(event)
    
    # Export metrics
    exported = await auth_metrics.export_metrics(
        format="json",
        start_time=datetime.utcnow() - timedelta(hours=1)
    )
    
    assert isinstance(exported, str)
    assert "login" in exported
    assert "token_validation" in exported

@pytest.mark.asyncio
async def test_performance_alerts(auth_metrics):
    # Record high-latency events
    slow_events = [
        AuthEvent(
            event_type="login",
            user_id="user123",
            timestamp=datetime.utcnow(),
            success=True,
            latency_ms=200,  # Above threshold
            details={}
        )
        for _ in range(5)
    ]
    
    alerts = []
    auth_metrics.on_performance_alert(lambda alert: alerts.append(alert))
    
    for event in slow_events:
        await auth_metrics.record_event(event)
    
    assert len(alerts) > 0
    assert alerts[0].metric == "auth_latency_ms"

@pytest.mark.asyncio
async def test_metrics_cleanup(auth_metrics):
    # Add old events
    old_event = AuthEvent(
        event_type="login",
        user_id="user123",
        timestamp=datetime.utcnow() - timedelta(days=2),
        success=True,
        latency_ms=50,
        details={}
    )
    
    await auth_metrics.record_event(old_event)
    
    # Run cleanup
    await auth_metrics.cleanup_old_events()
    
    assert len(auth_metrics.events) == 0

@pytest.mark.asyncio
async def test_metrics_persistence(auth_metrics):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        await auth_metrics.save_state()
        mock_file.write.assert_called_once()
        
        await auth_metrics.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_method_specific_metrics(auth_metrics):
    # Record events for different auth methods
    methods = ["password", "oauth", "token"]
    for method in methods:
        for _ in range(5):
            await auth_metrics.record_event(AuthEvent(
                event_type="login",
                user_id="user123",
                timestamp=datetime.utcnow(),
                success=True,
                latency_ms=50,
                details={"method": method}
            ))
    
    # Get metrics per method
    method_stats = await auth_metrics.get_method_stats()
    
    assert all(method in method_stats for method in methods)
    assert all(method_stats[method].success_count == 5 for method in methods)

@pytest.mark.asyncio
async def test_real_time_metrics(auth_metrics):
    # Record events in real-time
    start_time = datetime.utcnow()
    
    async def record_events():
        for i in range(10):
            await auth_metrics.record_event(AuthEvent(
                event_type="login",
                user_id=f"user{i}",
                timestamp=datetime.utcnow(),
                success=True,
                latency_ms=50,
                details={}
            ))
            await asyncio.sleep(0.1)
    
    # Start recording events
    await record_events()
    
    # Get real-time metrics
    realtime = await auth_metrics.get_realtime_metrics()
    
    assert realtime.events_per_second > 0
    assert realtime.active_users > 0

@pytest.mark.asyncio
async def test_error_pattern_detection(auth_metrics):
    # Record failed auth attempts with patterns
    for _ in range(10):
        await auth_metrics.record_event(AuthEvent(
            event_type="login",
            user_id="user123",
            timestamp=datetime.utcnow(),
            success=False,
            latency_ms=50,
            details={"error": "invalid_password"}
        ))
    
    patterns = await auth_metrics.detect_error_patterns()
    assert len(patterns) > 0
    assert "invalid_password" in patterns[0].error_type 