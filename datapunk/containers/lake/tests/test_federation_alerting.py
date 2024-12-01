import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import MagicMock, patch
from ..src.query.federation.alerting import (
    AlertSeverity,
    AlertRule,
    Alert,
    AlertManager,
    LoggingAlertHandler,
    WebhookAlertHandler,
    EmailAlertHandler,
    create_default_rules
)

@pytest.fixture
def alert_manager():
    """Create alert manager instance."""
    return AlertManager()

@pytest.fixture
def sample_metrics():
    """Create sample metrics data."""
    return {
        'execution_time_ms': 6000,
        'memory_usage_mb': 1200,
        'errors': ['Test error'],
        'source_metrics': {
            'source1': {'execution_time_ms': 11000},
            'source2': {'execution_time_ms': 5000}
        },
        'merge_metrics': {'error': None}
    }

class TestAlertRules:
    """Test cases for alert rules."""
    
    def test_rule_creation(self):
        """Test alert rule creation."""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: m.get('value', 0) > 100,
            message_template="Value {value} exceeds threshold",
            severity=AlertSeverity.WARNING
        )
        
        assert rule.name == "test_rule"
        assert rule.severity == AlertSeverity.WARNING
        assert rule.cooldown == timedelta(minutes=5)
        
    def test_default_rules(self):
        """Test default alert rules."""
        rules = create_default_rules()
        
        assert len(rules) >= 5  # At least 5 default rules
        assert any(r.name == "high_execution_time" for r in rules)
        assert any(r.name == "memory_usage" for r in rules)

class TestAlertHandlers:
    """Test cases for alert handlers."""
    
    @pytest.fixture
    def sample_alert(self):
        """Create sample alert."""
        return Alert(
            rule_name="test_rule",
            message="Test alert message",
            severity=AlertSeverity.WARNING,
            timestamp=datetime.now(),
            context={'value': 150},
            query_id="test_query"
        )
        
    def test_logging_handler(self, sample_alert):
        """Test logging alert handler."""
        with patch('logging.Logger.log') as mock_log:
            handler = LoggingAlertHandler()
            handler.handle_alert(sample_alert)
            
            mock_log.assert_called_once()
            args = mock_log.call_args[0]
            assert "WARNING" in args[1]
            assert sample_alert.message in args[1]
            
    def test_webhook_handler(self, sample_alert):
        """Test webhook alert handler."""
        with patch('requests.Session.post') as mock_post:
            handler = WebhookAlertHandler("http://test.com/webhook")
            handler.handle_alert(sample_alert)
            
            mock_post.assert_called_once()
            payload = mock_post.call_args[1]['json']
            assert payload['severity'] == sample_alert.severity.value
            assert payload['message'] == sample_alert.message
            
    def test_email_handler(self, sample_alert):
        """Test email alert handler."""
        with patch('smtplib.SMTP') as mock_smtp:
            handler = EmailAlertHandler(
                smtp_host="test.com",
                smtp_port=587,
                sender="test@test.com",
                recipients=["admin@test.com"]
            )
            handler.handle_alert(sample_alert)
            
            mock_smtp.assert_called_once()
            instance = mock_smtp.return_value.__enter__.return_value
            assert instance.send_message.called

class TestAlertManager:
    """Test cases for alert manager."""
    
    def test_rule_management(self, alert_manager):
        """Test rule addition and removal."""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: True,
            message_template="Test message",
            severity=AlertSeverity.INFO
        )
        
        alert_manager.add_rule(rule)
        assert "test_rule" in alert_manager.rules
        
        alert_manager.remove_rule("test_rule")
        assert "test_rule" not in alert_manager.rules
        
    def test_handler_management(self, alert_manager):
        """Test handler addition."""
        handler = LoggingAlertHandler()
        alert_manager.add_handler(handler)
        assert handler in alert_manager.handlers
        
    def test_condition_checking(self, alert_manager, sample_metrics):
        """Test alert condition checking."""
        # Add test rule
        rule = AlertRule(
            name="high_memory",
            condition=lambda m: m.get('memory_usage_mb', 0) > 1000,
            message_template="High memory usage: {memory_usage_mb}MB",
            severity=AlertSeverity.WARNING
        )
        alert_manager.add_rule(rule)
        
        # Add mock handler
        mock_handler = MagicMock()
        alert_manager.add_handler(mock_handler)
        
        # Check conditions
        alert_manager.check_conditions(sample_metrics, "test_query")
        
        # Verify handler was called
        mock_handler.handle_alert.assert_called_once()
        alert = mock_handler.handle_alert.call_args[0][0]
        assert alert.rule_name == "high_memory"
        assert alert.severity == AlertSeverity.WARNING
        
    def test_cooldown_period(self, alert_manager, sample_metrics):
        """Test alert cooldown period."""
        # Add test rule with short cooldown
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: True,
            message_template="Test message",
            severity=AlertSeverity.INFO,
            cooldown=timedelta(seconds=1)
        )
        alert_manager.add_rule(rule)
        
        # Add mock handler
        mock_handler = MagicMock()
        alert_manager.add_handler(mock_handler)
        
        # First alert
        alert_manager.check_conditions(sample_metrics)
        assert mock_handler.handle_alert.call_count == 1
        
        # Immediate second alert (should be suppressed)
        alert_manager.check_conditions(sample_metrics)
        assert mock_handler.handle_alert.call_count == 1
        
        # Wait for cooldown
        import time
        time.sleep(1.1)
        
        # Third alert (should trigger)
        alert_manager.check_conditions(sample_metrics)
        assert mock_handler.handle_alert.call_count == 2
        
    def test_multiple_handlers(self, alert_manager, sample_metrics):
        """Test multiple alert handlers."""
        # Add test rule
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: True,
            message_template="Test message",
            severity=AlertSeverity.INFO
        )
        alert_manager.add_rule(rule)
        
        # Add multiple mock handlers
        mock_handlers = [MagicMock() for _ in range(3)]
        for handler in mock_handlers:
            alert_manager.add_handler(handler)
            
        # Check conditions
        alert_manager.check_conditions(sample_metrics)
        
        # Verify all handlers were called
        for handler in mock_handlers:
            handler.handle_alert.assert_called_once() 