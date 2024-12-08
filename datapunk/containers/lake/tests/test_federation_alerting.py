import pytest
import asyncio
from datetime import datetime, timedelta
from ..src.query.federation.fed_alerting import (
    AlertManager,
    AlertRule,
    Alert,
    AlertSeverity,
    AlertType,
    create_default_rules
)

@pytest.fixture
def alert_manager():
    return AlertManager()

@pytest.fixture
def sample_metrics():
    return {
        'error_rate': 0.05,
        'avg_execution_time_ms': 500,
        'cache_hit_ratio': 0.7,
        'memory_usage_mb': 800,
        'source_stats': {
            'source1': {'status': 'healthy'},
            'source2': {'status': 'healthy'}
        }
    }

@pytest.fixture
def test_rule():
    return AlertRule(
        name="test_rule",
        description="Test alert rule",
        severity=AlertSeverity.WARNING,
        alert_type=AlertType.PERFORMANCE,
        condition=lambda m: m.get('test_value', 0) > 100
    )

def test_alert_handler(alert: Alert):
    """Test alert handler function."""
    pass

@pytest.mark.asyncio
async def test_alert_lifecycle(alert_manager, test_rule):
    """Test complete alert lifecycle."""
    # Add rule and handler
    alert_manager.add_rule(test_rule)
    alert_manager.add_handler(AlertSeverity.WARNING, test_alert_handler)
    
    # Test metrics that don't trigger alert
    await alert_manager.check_conditions({'test_value': 50})
    assert len(alert_manager.active_alerts) == 0
    
    # Test metrics that trigger alert
    await alert_manager.check_conditions({'test_value': 150})
    assert len(alert_manager.active_alerts) == 1
    
    # Resolve alert
    await alert_manager.resolve_alert(0, "Issue resolved")
    assert len(alert_manager.active_alerts) == 0
    assert len(alert_manager.alert_history) == 1
    
    # Verify resolved alert
    alert = alert_manager.alert_history[0]
    assert alert.resolved
    assert alert.resolution_message == "Issue resolved"
    assert alert.resolved_at is not None

@pytest.mark.asyncio
async def test_alert_cooldown(alert_manager, test_rule):
    """Test alert cooldown period."""
    alert_manager.add_rule(test_rule)
    
    # Trigger first alert
    await alert_manager.check_conditions({'test_value': 150})
    assert len(alert_manager.active_alerts) == 1
    
    # Try to trigger again immediately
    await alert_manager.check_conditions({'test_value': 150})
    assert len(alert_manager.active_alerts) == 1  # Should not create new alert
    
    # Wait for cooldown
    test_rule.last_triggered = datetime.utcnow() - timedelta(minutes=20)
    
    # Should trigger new alert
    await alert_manager.check_conditions({'test_value': 150})
    assert len(alert_manager.active_alerts) == 2

@pytest.mark.asyncio
async def test_default_rules(alert_manager, sample_metrics):
    """Test default alert rules."""
    # Add default rules
    for rule in create_default_rules():
        alert_manager.add_rule(rule)
    
    # Test with normal metrics
    await alert_manager.check_conditions(sample_metrics)
    assert len(alert_manager.active_alerts) == 0
    
    # Test with problematic metrics
    problematic_metrics = sample_metrics.copy()
    problematic_metrics.update({
        'error_rate': 0.15,  # Should trigger high_error_rate
        'avg_execution_time_ms': 1500,  # Should trigger high_latency
        'memory_usage_mb': 1200  # Should trigger high_memory_usage
    })
    
    await alert_manager.check_conditions(problematic_metrics)
    assert len(alert_manager.active_alerts) == 3

@pytest.mark.asyncio
async def test_alert_filtering(alert_manager):
    """Test alert filtering capabilities."""
    # Create alerts of different types
    alerts = [
        Alert(
            rule_name=f"rule_{i}",
            severity=AlertSeverity.WARNING if i % 2 else AlertSeverity.ERROR,
            alert_type=AlertType.PERFORMANCE if i % 2 else AlertType.ERROR,
            message=f"Test alert {i}",
            timestamp=datetime.utcnow(),
            context={}
        )
        for i in range(4)
    ]
    
    # Add to active alerts
    alert_manager.active_alerts.extend(alerts)
    
    # Test filtering by severity
    warning_alerts = alert_manager.get_active_alerts(
        severity=AlertSeverity.WARNING
    )
    assert len(warning_alerts) == 2
    
    # Test filtering by type
    performance_alerts = alert_manager.get_active_alerts(
        alert_type=AlertType.PERFORMANCE
    )
    assert len(performance_alerts) == 2

@pytest.mark.asyncio
async def test_alert_history(alert_manager):
    """Test alert history management."""
    # Create historical alerts
    now = datetime.utcnow()
    old_alerts = [
        Alert(
            rule_name=f"old_rule_{i}",
            severity=AlertSeverity.WARNING,
            alert_type=AlertType.PERFORMANCE,
            message=f"Old alert {i}",
            timestamp=now - timedelta(days=35),  # Older than retention period
            context={},
            resolved=True,
            resolved_at=now - timedelta(days=34)
        )
        for i in range(3)
    ]
    
    recent_alerts = [
        Alert(
            rule_name=f"recent_rule_{i}",
            severity=AlertSeverity.ERROR,
            alert_type=AlertType.ERROR,
            message=f"Recent alert {i}",
            timestamp=now - timedelta(days=1),
            context={},
            resolved=True,
            resolved_at=now
        )
        for i in range(2)
    ]
    
    alert_manager.alert_history.extend(old_alerts + recent_alerts)
    
    # Test history trimming
    await alert_manager._trim_history()
    assert len(alert_manager.alert_history) == 2  # Only recent alerts remain

@pytest.mark.asyncio
async def test_alert_stats(alert_manager):
    """Test alert statistics generation."""
    # Create alerts with different properties
    now = datetime.utcnow()
    alerts = [
        Alert(
            rule_name=f"rule_{i}",
            severity=AlertSeverity.WARNING if i % 2 else AlertSeverity.ERROR,
            alert_type=AlertType.PERFORMANCE if i % 2 else AlertType.ERROR,
            message=f"Test alert {i}",
            timestamp=now - timedelta(hours=1),
            context={},
            resolved=i < 3,  # Some resolved, some not
            resolved_at=now if i < 3 else None
        )
        for i in range(5)
    ]
    
    alert_manager.alert_history.extend(alerts)
    
    # Get stats
    stats = alert_manager.get_alert_stats(hours=2)
    
    assert stats['total_alerts'] == 5
    assert stats['unresolved_alerts'] == 2
    assert stats['alerts_by_severity']['warning'] == 2
    assert stats['alerts_by_severity']['error'] == 3
    assert 'avg_resolution_time_minutes' in stats

@pytest.mark.asyncio
async def test_error_handling(alert_manager, test_rule):
    """Test error handling in alerting system."""
    # Add rule with problematic condition
    bad_rule = AlertRule(
        name="bad_rule",
        description="Rule that raises exception",
        severity=AlertSeverity.ERROR,
        alert_type=AlertType.ERROR,
        condition=lambda m: 1/0  # Will raise ZeroDivisionError
    )
    
    alert_manager.add_rule(bad_rule)
    alert_manager.add_rule(test_rule)  # Add good rule too
    
    # Check conditions should continue despite error
    await alert_manager.check_conditions({'test_value': 150})
    assert len(alert_manager.active_alerts) == 1  # Good rule should still work
    
    # Test error in handler
    def bad_handler(alert: Alert):
        raise Exception("Handler error")
    
    alert_manager.add_handler(AlertSeverity.WARNING, bad_handler)
    await alert_manager.check_conditions({'test_value': 150})
    assert len(alert_manager.active_alerts) == 2  # Alert should still be created 