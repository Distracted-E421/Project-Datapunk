import pytest
import asyncio
from datetime import datetime, timedelta
from datapunk.lib.monitoring.alert_manager import (
    AlertSeverity, AlertStatus, AlertRule, Alert,
    NotificationChannel, AlertManager
)

class MockNotificationChannel(NotificationChannel):
    def __init__(self, should_succeed: bool = True):
        self.notifications = []
        self.should_succeed = should_succeed

    async def send_notification(self, alert: Alert) -> bool:
        self.notifications.append(alert)
        return self.should_succeed

@pytest.fixture
def alert_rule():
    async def condition():
        return True
    
    return AlertRule(
        name="test_rule",
        description="Test alert rule",
        severity=AlertSeverity.HIGH,
        condition=condition,
        check_interval=timedelta(seconds=1),
        timeout=timedelta(seconds=5)
    )

@pytest.fixture
def alert_manager():
    return AlertManager()

@pytest.fixture
def mock_channel():
    return MockNotificationChannel()

@pytest.fixture
def failing_channel():
    return MockNotificationChannel(should_succeed=False)

@pytest.mark.asyncio
async def test_add_remove_rule(alert_manager, alert_rule):
    alert_manager.add_rule(alert_rule)
    assert "test_rule" in alert_manager.rules
    
    alert_manager.remove_rule("test_rule")
    assert "test_rule" not in alert_manager.rules

def test_duplicate_rule(alert_manager, alert_rule):
    alert_manager.add_rule(alert_rule)
    with pytest.raises(ValueError, match="already exists"):
        alert_manager.add_rule(alert_rule)

@pytest.mark.asyncio
async def test_notification_channel_management(alert_manager, mock_channel):
    # Test adding channel
    alert_manager.add_notification_channel(AlertSeverity.HIGH, mock_channel)
    assert mock_channel in alert_manager.notification_channels[AlertSeverity.HIGH]
    
    # Test adding to multiple severities
    alert_manager.add_notification_channel(
        [AlertSeverity.MEDIUM, AlertSeverity.LOW],
        mock_channel
    )
    assert mock_channel in alert_manager.notification_channels[AlertSeverity.MEDIUM]
    assert mock_channel in alert_manager.notification_channels[AlertSeverity.LOW]
    
    # Test removing channel
    alert_manager.remove_notification_channel(AlertSeverity.HIGH, mock_channel)
    assert mock_channel not in alert_manager.notification_channels[AlertSeverity.HIGH]
    
    # Test removing from multiple severities
    alert_manager.remove_notification_channel(
        [AlertSeverity.MEDIUM, AlertSeverity.LOW],
        mock_channel
    )
    assert mock_channel not in alert_manager.notification_channels[AlertSeverity.MEDIUM]
    assert mock_channel not in alert_manager.notification_channels[AlertSeverity.LOW]

@pytest.mark.asyncio
async def test_alert_generation(alert_manager, alert_rule, mock_channel):
    alert_manager.add_rule(alert_rule)
    alert_manager.add_notification_channel(AlertSeverity.HIGH, mock_channel)
    
    await alert_manager.start()
    await asyncio.sleep(1.1)  # Wait for first check
    
    # Verify alert was generated
    alerts = alert_manager.get_active_alerts()
    assert len(alerts) == 1
    assert alerts[0].rule_name == "test_rule"
    assert alerts[0].status == AlertStatus.ACTIVE
    
    # Verify notification was sent
    assert len(mock_channel.notifications) == 1
    assert mock_channel.notifications[0].rule_name == "test_rule"
    
    await alert_manager.stop()

@pytest.mark.asyncio
async def test_alert_lifecycle(alert_manager, alert_rule):
    alert_manager.add_rule(alert_rule)
    await alert_manager.start()
    await asyncio.sleep(1.1)  # Wait for alert generation
    
    # Test acknowledgment
    await alert_manager.acknowledge_alert("test_rule", "test_user")
    alert = alert_manager.get_alert("test_rule")
    assert alert.status == AlertStatus.ACKNOWLEDGED
    assert alert.acknowledged_by == "test_user"
    
    # Test resolution
    await alert_manager.resolve_alert(
        "test_rule",
        "test_resolver",
        "Issue fixed"
    )
    assert "test_rule" not in alert_manager.active_alerts
    
    await alert_manager.stop()

@pytest.mark.asyncio
async def test_failed_notifications(alert_manager, alert_rule, failing_channel):
    alert_manager.add_rule(alert_rule)
    alert_manager.add_notification_channel(AlertSeverity.HIGH, failing_channel)
    
    await alert_manager.start()
    await asyncio.sleep(1.1)  # Wait for alert generation
    
    # Verify notification attempt
    assert len(failing_channel.notifications) == 1
    
    await alert_manager.stop()

@pytest.mark.asyncio
async def test_alert_filtering(alert_manager):
    # Create rules with different severities
    async def condition():
        return True
    
    rules = [
        AlertRule(
            name=f"rule_{sev.name.lower()}",
            description=f"Test {sev.name.lower()} rule",
            severity=sev,
            condition=condition,
            check_interval=timedelta(seconds=1),
            timeout=timedelta(seconds=5)
        )
        for sev in [AlertSeverity.HIGH, AlertSeverity.MEDIUM, AlertSeverity.LOW]
    ]
    
    for rule in rules:
        alert_manager.add_rule(rule)
    
    await alert_manager.start()
    await asyncio.sleep(1.1)  # Wait for alert generation
    
    # Test filtering by severity
    high_alerts = alert_manager.get_active_alerts(AlertSeverity.HIGH)
    assert len(high_alerts) == 1
    assert high_alerts[0].rule_name == "rule_high"
    
    medium_alerts = alert_manager.get_active_alerts(AlertSeverity.MEDIUM)
    assert len(medium_alerts) == 1
    assert medium_alerts[0].rule_name == "rule_medium"
    
    # Test getting all alerts
    all_alerts = alert_manager.get_active_alerts()
    assert len(all_alerts) == 3
    
    await alert_manager.stop()

@pytest.mark.asyncio
async def test_alert_auto_resolution(alert_manager):
    # Create a rule that alternates between True and False
    toggle = True
    async def condition():
        nonlocal toggle
        toggle = not toggle
        return toggle
    
    rule = AlertRule(
        name="toggle_rule",
        description="Test toggle rule",
        severity=AlertSeverity.HIGH,
        condition=condition,
        check_interval=timedelta(seconds=1),
        timeout=timedelta(seconds=5)
    )
    
    alert_manager.add_rule(rule)
    await alert_manager.start()
    
    # Wait for first alert
    await asyncio.sleep(1.1)
    assert "toggle_rule" in alert_manager.active_alerts
    
    # Wait for auto-resolution
    await asyncio.sleep(1.1)
    assert "toggle_rule" not in alert_manager.active_alerts
    
    await alert_manager.stop()

@pytest.mark.asyncio
async def test_invalid_alert_operations(alert_manager):
    # Test acknowledging non-existent alert
    with pytest.raises(ValueError, match="No active alert found"):
        await alert_manager.acknowledge_alert("nonexistent", "test_user")
    
    # Test resolving non-existent alert (should not raise)
    await alert_manager.resolve_alert("nonexistent", "test_user")
    
    # Create an alert and resolve it
    async def condition():
        return True
    
    rule = AlertRule(
        name="test_rule",
        description="Test rule",
        severity=AlertSeverity.HIGH,
        condition=condition,
        check_interval=timedelta(seconds=1),
        timeout=timedelta(seconds=5)
    )
    
    alert_manager.add_rule(rule)
    await alert_manager.start()
    await asyncio.sleep(1.1)
    
    await alert_manager.resolve_alert("test_rule", "test_user")
    
    # Try to acknowledge resolved alert
    with pytest.raises(ValueError, match="not in ACTIVE status"):
        await alert_manager.acknowledge_alert("test_rule", "test_user")
    
    await alert_manager.stop() 