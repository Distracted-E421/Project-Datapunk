import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.auth import (
    SecurityMetrics,
    MetricsConfig,
    SecurityEvent,
    MetricsAggregator,
    SecurityAlert
)

@pytest.fixture
def metrics_config():
    return MetricsConfig(
        collection_interval=60,  # 1 minute
        retention_period=86400,  # 1 day
        alert_thresholds={
            "failed_auth": 5,
            "suspicious_ips": 3,
            "error_rate": 0.1
        }
    )

@pytest.fixture
def security_metrics(metrics_config):
    return SecurityMetrics(config=metrics_config)

@pytest.fixture
def sample_events():
    return [
        SecurityEvent(
            event_type="failed_auth",
            source_ip="192.168.1.100",
            timestamp=datetime.utcnow(),
            details={"reason": "invalid_token"}
        ),
        SecurityEvent(
            event_type="suspicious_activity",
            source_ip="192.168.1.101",
            timestamp=datetime.utcnow(),
            details={"pattern": "sql_injection"}
        )
    ]

@pytest.mark.asyncio
async def test_metrics_initialization(security_metrics, metrics_config):
    assert security_metrics.config == metrics_config
    assert not security_metrics.is_collecting
    assert len(security_metrics.events) == 0

@pytest.mark.asyncio
async def test_event_collection(security_metrics, sample_events):
    for event in sample_events:
        await security_metrics.record_event(event)
    
    assert len(security_metrics.events) == len(sample_events)
    assert all(e.event_type in ["failed_auth", "suspicious_activity"] 
              for e in security_metrics.events)

@pytest.mark.asyncio
async def test_metrics_aggregation(security_metrics, sample_events):
    # Record multiple events
    for event in sample_events * 3:  # Triple the events
        await security_metrics.record_event(event)
    
    # Aggregate metrics
    aggregated = await security_metrics.aggregate_metrics(
        start_time=datetime.utcnow() - timedelta(hours=1)
    )
    
    assert "failed_auth" in aggregated
    assert "suspicious_activity" in aggregated
    assert aggregated["failed_auth"]["count"] == 3
    assert aggregated["suspicious_activity"]["count"] == 3

@pytest.mark.asyncio
async def test_alert_generation(security_metrics):
    alerts = []
    
    def alert_handler(alert: SecurityAlert):
        alerts.append(alert)
    
    security_metrics.on_alert(alert_handler)
    
    # Generate multiple failed auth events
    for _ in range(6):  # Exceeds threshold of 5
        await security_metrics.record_event(SecurityEvent(
            event_type="failed_auth",
            source_ip="192.168.1.100",
            timestamp=datetime.utcnow(),
            details={"reason": "invalid_token"}
        ))
    
    assert len(alerts) > 0
    assert alerts[0].event_type == "failed_auth"
    assert alerts[0].severity == "high"

@pytest.mark.asyncio
async def test_metrics_cleanup(security_metrics, sample_events):
    # Add old events
    old_events = [
        SecurityEvent(
            event_type=e.event_type,
            source_ip=e.source_ip,
            timestamp=datetime.utcnow() - timedelta(days=2),  # Older than retention
            details=e.details
        )
        for e in sample_events
    ]
    
    for event in old_events:
        await security_metrics.record_event(event)
    
    # Run cleanup
    await security_metrics.cleanup_old_events()
    
    assert len(security_metrics.events) == 0

@pytest.mark.asyncio
async def test_ip_based_metrics(security_metrics):
    # Record events from multiple IPs
    ips = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]
    for ip in ips:
        for _ in range(3):
            await security_metrics.record_event(SecurityEvent(
                event_type="failed_auth",
                source_ip=ip,
                timestamp=datetime.utcnow(),
                details={"reason": "invalid_token"}
            ))
    
    # Get metrics per IP
    ip_metrics = await security_metrics.get_ip_metrics()
    
    assert len(ip_metrics) == len(ips)
    assert all(ip in ip_metrics for ip in ips)
    assert all(ip_metrics[ip]["failed_auth"] == 3 for ip in ips)

@pytest.mark.asyncio
async def test_metrics_export(security_metrics, sample_events):
    for event in sample_events:
        await security_metrics.record_event(event)
    
    # Export metrics
    exported = await security_metrics.export_metrics(
        format="json",
        start_time=datetime.utcnow() - timedelta(hours=1)
    )
    
    assert isinstance(exported, str)
    assert "failed_auth" in exported
    assert "suspicious_activity" in exported

@pytest.mark.asyncio
async def test_concurrent_event_recording(security_metrics):
    # Generate multiple events
    events = [
        SecurityEvent(
            event_type="failed_auth",
            source_ip=f"192.168.1.{i}",
            timestamp=datetime.utcnow(),
            details={"reason": "invalid_token"}
        )
        for i in range(100)
    ]
    
    # Record events concurrently
    await asyncio.gather(*[
        security_metrics.record_event(event)
        for event in events
    ])
    
    assert len(security_metrics.events) == 100

@pytest.mark.asyncio
async def test_metrics_persistence(security_metrics):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        # Save metrics state
        await security_metrics.save_state()
        mock_file.write.assert_called_once()
        
        # Load metrics state
        await security_metrics.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_metrics_aggregation_window(security_metrics, sample_events):
    # Record events with different timestamps
    now = datetime.utcnow()
    
    events = [
        SecurityEvent(
            event_type=e.event_type,
            source_ip=e.source_ip,
            timestamp=now - timedelta(minutes=i),
            details=e.details
        )
        for i, e in enumerate(sample_events * 3)
    ]
    
    for event in events:
        await security_metrics.record_event(event)
    
    # Aggregate with different time windows
    last_hour = await security_metrics.aggregate_metrics(
        start_time=now - timedelta(hours=1)
    )
    last_minute = await security_metrics.aggregate_metrics(
        start_time=now - timedelta(minutes=1)
    )
    
    assert last_hour["failed_auth"]["count"] > last_minute["failed_auth"]["count"]

@pytest.mark.asyncio
async def test_metrics_rate_calculation(security_metrics):
    start_time = datetime.utcnow()
    
    # Record events over time
    for i in range(60):  # One event per second for a minute
        await security_metrics.record_event(SecurityEvent(
            event_type="failed_auth",
            source_ip="192.168.1.100",
            timestamp=start_time + timedelta(seconds=i),
            details={"reason": "invalid_token"}
        ))
    
    # Calculate rates
    rates = await security_metrics.calculate_event_rates(
        start_time=start_time,
        end_time=start_time + timedelta(minutes=1)
    )
    
    assert "failed_auth" in rates
    assert abs(rates["failed_auth"] - 1.0) < 0.1  # Approximately 1 event per second

@pytest.mark.asyncio
async def test_alert_threshold_updates(security_metrics):
    # Update alert thresholds
    new_thresholds = {
        "failed_auth": 10,
        "suspicious_ips": 5,
        "error_rate": 0.2
    }
    
    await security_metrics.update_alert_thresholds(new_thresholds)
    
    # Verify thresholds are updated
    assert security_metrics.config.alert_thresholds == new_thresholds

@pytest.mark.asyncio
async def test_metrics_summary_generation(security_metrics, sample_events):
    for event in sample_events:
        await security_metrics.record_event(event)
    
    summary = await security_metrics.generate_summary(
        start_time=datetime.utcnow() - timedelta(hours=1)
    )
    
    assert "total_events" in summary
    assert "event_types" in summary
    assert "unique_ips" in summary
    assert summary["total_events"] == len(sample_events) 