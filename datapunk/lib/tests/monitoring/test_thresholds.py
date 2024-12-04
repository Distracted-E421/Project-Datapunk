import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.monitoring.thresholds import (
    ThresholdMonitor,
    ThresholdConfig,
    ThresholdType,
    AlertLevel
)
from datapunk_shared.monitoring import MetricsClient
from datapunk.lib.tracing import TracingManager

@pytest.fixture
def threshold_config():
    return ThresholdConfig(
        name="test_thresholds",
        check_interval=5,  # seconds
        thresholds=[
            {
                "name": "cpu_usage",
                "type": ThresholdType.PERCENTAGE,
                "warning": 70,
                "critical": 90,
                "duration": 300  # 5 minutes
            },
            {
                "name": "memory_usage",
                "type": ThresholdType.BYTES,
                "warning": 8 * 1024 * 1024 * 1024,  # 8GB
                "critical": 12 * 1024 * 1024 * 1024,  # 12GB
                "duration": 600  # 10 minutes
            }
        ]
    )

@pytest.fixture
def mock_metrics():
    return MagicMock(spec=MetricsClient)

@pytest.fixture
def mock_tracing():
    return MagicMock(spec=TracingManager)

@pytest.fixture
async def threshold_monitor(threshold_config, mock_metrics, mock_tracing):
    monitor = ThresholdMonitor(threshold_config, mock_metrics, mock_tracing)
    await monitor.initialize()
    return monitor

@pytest.mark.asyncio
async def test_monitor_initialization(threshold_monitor, threshold_config):
    """Test threshold monitor initialization"""
    assert threshold_monitor.config == threshold_config
    assert not threshold_monitor.is_stopped
    assert len(threshold_monitor.thresholds) == len(threshold_config.thresholds)

@pytest.mark.asyncio
async def test_threshold_check_percentage(threshold_monitor):
    """Test percentage threshold checking"""
    # Test CPU usage threshold
    value = 85.0  # Between warning and critical
    result = await threshold_monitor.check_threshold("cpu_usage", value)
    
    assert result.alert_level == AlertLevel.WARNING
    assert result.threshold_name == "cpu_usage"
    assert result.current_value == value
    
    # Verify metrics
    threshold_monitor.metrics.gauge.assert_called_with(
        'threshold_value',
        value,
        {'monitor': threshold_monitor.config.name, 'threshold': 'cpu_usage'}
    )

@pytest.mark.asyncio
async def test_threshold_check_bytes(threshold_monitor):
    """Test bytes threshold checking"""
    # Test memory usage threshold
    value = 10 * 1024 * 1024 * 1024  # 10GB - Between warning and critical
    result = await threshold_monitor.check_threshold("memory_usage", value)
    
    assert result.alert_level == AlertLevel.WARNING
    assert result.threshold_name == "memory_usage"
    assert result.current_value == value
    
    # Verify metrics
    threshold_monitor.metrics.gauge.assert_called_with(
        'threshold_value',
        value,
        {'monitor': threshold_monitor.config.name, 'threshold': 'memory_usage'}
    )

@pytest.mark.asyncio
async def test_duration_based_alerts(threshold_monitor):
    """Test duration-based threshold alerts"""
    # Simulate sustained high CPU usage
    high_value = 95.0  # Above critical
    
    # Record multiple readings
    for _ in range(5):
        result = await threshold_monitor.check_threshold("cpu_usage", high_value)
        await asyncio.sleep(0.1)
    
    # Verify sustained alert
    assert result.alert_level == AlertLevel.CRITICAL
    assert result.duration >= threshold_monitor.get_threshold("cpu_usage").duration
    
    # Verify alert metrics
    threshold_monitor.metrics.increment.assert_called_with(
        'threshold_critical_alerts_total',
        {'monitor': threshold_monitor.config.name, 'threshold': 'cpu_usage'}
    )

@pytest.mark.asyncio
async def test_threshold_recovery(threshold_monitor):
    """Test threshold recovery detection"""
    # First trigger warning
    await threshold_monitor.check_threshold("cpu_usage", 75.0)
    
    # Then recover
    result = await threshold_monitor.check_threshold("cpu_usage", 50.0)
    
    assert result.alert_level == AlertLevel.NORMAL
    assert result.recovered
    
    # Verify recovery metrics
    threshold_monitor.metrics.increment.assert_called_with(
        'threshold_recoveries_total',
        {'monitor': threshold_monitor.config.name, 'threshold': 'cpu_usage'}
    )

@pytest.mark.asyncio
async def test_threshold_trends(threshold_monitor):
    """Test threshold trend analysis"""
    # Simulate increasing values
    values = [60.0, 65.0, 70.0, 75.0]
    
    for value in values:
        await threshold_monitor.check_threshold("cpu_usage", value)
    
    # Get trend analysis
    trend = threshold_monitor.analyze_trend("cpu_usage")
    
    assert trend.is_increasing
    assert trend.rate_of_change == 5.0  # Average increase
    
    # Verify trend metrics
    threshold_monitor.metrics.gauge.assert_any_call(
        'threshold_trend',
        5.0,
        {'monitor': threshold_monitor.config.name, 'threshold': 'cpu_usage'}
    )

@pytest.mark.asyncio
async def test_composite_thresholds(threshold_monitor):
    """Test composite threshold checking"""
    # Add composite threshold
    composite_config = {
        "name": "system_health",
        "type": ThresholdType.COMPOSITE,
        "warning": 2,  # Number of individual warnings
        "critical": 3,  # Number of individual criticals
        "components": ["cpu_usage", "memory_usage"]
    }
    threshold_monitor.add_threshold(composite_config)
    
    # Trigger multiple thresholds
    await threshold_monitor.check_threshold("cpu_usage", 75.0)  # Warning
    await threshold_monitor.check_threshold("memory_usage", 13 * 1024 * 1024 * 1024)  # Critical
    
    # Check composite result
    result = await threshold_monitor.check_composite_threshold("system_health")
    
    assert result.alert_level == AlertLevel.WARNING
    assert len(result.component_results) == 2

@pytest.mark.asyncio
async def test_error_handling(threshold_monitor):
    """Test error handling"""
    # Test invalid threshold name
    with pytest.raises(ValueError):
        await threshold_monitor.check_threshold("invalid_threshold", 50.0)
    
    # Test invalid value type
    with pytest.raises(ValueError):
        await threshold_monitor.check_threshold("cpu_usage", "invalid_value")
    
    # Verify error metrics
    threshold_monitor.metrics.increment.assert_called_with(
        'threshold_check_errors_total',
        {'monitor': threshold_monitor.config.name}
    )

@pytest.mark.asyncio
async def test_threshold_history(threshold_monitor):
    """Test threshold history tracking"""
    # Record multiple values
    values = [50.0, 60.0, 70.0]
    for value in values:
        await threshold_monitor.check_threshold("cpu_usage", value)
    
    # Get history
    history = threshold_monitor.get_threshold_history("cpu_usage")
    
    assert len(history) == len(values)
    assert all(entry.value in values for entry in history)
    
    # Verify history metrics
    threshold_monitor.metrics.histogram.assert_called_with(
        'threshold_history_values',
        {'monitor': threshold_monitor.config.name, 'threshold': 'cpu_usage'},
        buckets=[50.0, 60.0, 70.0]
    )

@pytest.mark.asyncio
async def test_alert_notifications(threshold_monitor):
    """Test alert notifications"""
    # Mock notification handler
    notification_handler = AsyncMock()
    threshold_monitor.set_notification_handler(notification_handler)
    
    # Trigger critical alert
    await threshold_monitor.check_threshold("cpu_usage", 95.0)
    
    # Verify notification
    notification_handler.assert_called_once()
    alert = notification_handler.call_args[0][0]
    assert alert.level == AlertLevel.CRITICAL
    assert alert.threshold_name == "cpu_usage"

@pytest.mark.asyncio
async def test_tracing_integration(threshold_monitor):
    """Test tracing integration"""
    # Check threshold
    await threshold_monitor.check_threshold("cpu_usage", 75.0)
    
    # Verify tracing attributes
    threshold_monitor.tracing.set_attribute.assert_any_call(
        'threshold.name', 'cpu_usage'
    )
    threshold_monitor.tracing.set_attribute.assert_any_call(
        'threshold.value', 75.0
    )
    threshold_monitor.tracing.set_attribute.assert_any_call(
        'threshold.alert_level', AlertLevel.WARNING.value
    ) 