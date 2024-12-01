from typing import Any, Dict, List, Optional, Set, Union, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import logging
import json
from enum import Enum

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AlertRule:
    """Rule for generating alerts."""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    message_template: str
    severity: AlertSeverity
    cooldown: timedelta = timedelta(minutes=5)

@dataclass
class Alert:
    """Represents a monitoring alert."""
    rule_name: str
    message: str
    severity: AlertSeverity
    timestamp: datetime
    context: Dict[str, Any]
    query_id: Optional[str] = None

class AlertHandler:
    """Base class for alert handlers."""
    
    def handle_alert(self, alert: Alert) -> None:
        """Handle an alert."""
        raise NotImplementedError

class LoggingAlertHandler(AlertHandler):
    """Handles alerts by logging them."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def handle_alert(self, alert: Alert) -> None:
        """Log the alert with appropriate level."""
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }[alert.severity]
        
        self.logger.log(
            log_level,
            f"[{alert.severity.value.upper()}] {alert.message}",
            extra={
                'alert_context': alert.context,
                'query_id': alert.query_id,
                'timestamp': alert.timestamp.isoformat()
            }
        )

class WebhookAlertHandler(AlertHandler):
    """Handles alerts by sending them to a webhook."""
    
    def __init__(self, webhook_url: str):
        import requests
        self.webhook_url = webhook_url
        self._session = requests.Session()
        
    def handle_alert(self, alert: Alert) -> None:
        """Send alert to webhook."""
        payload = {
            'severity': alert.severity.value,
            'message': alert.message,
            'timestamp': alert.timestamp.isoformat(),
            'context': alert.context,
            'query_id': alert.query_id
        }
        
        try:
            response = self._session.post(
                self.webhook_url,
                json=payload,
                timeout=5
            )
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Failed to send alert to webhook: {e}")

class EmailAlertHandler(AlertHandler):
    """Handles alerts by sending emails."""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        sender: str,
        recipients: List[str],
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        import smtplib
        from email.mime.text import MIMEText
        
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender = sender
        self.recipients = recipients
        self.username = username
        self.password = password
        
    def handle_alert(self, alert: Alert) -> None:
        """Send alert via email."""
        import smtplib
        from email.mime.text import MIMEText
        
        # Create message
        body = f"""
        Alert: {alert.rule_name}
        Severity: {alert.severity.value}
        Time: {alert.timestamp.isoformat()}
        Message: {alert.message}
        
        Context:
        {json.dumps(alert.context, indent=2)}
        """
        
        msg = MIMEText(body)
        msg['Subject'] = f"[{alert.severity.value.upper()}] Query Federation Alert"
        msg['From'] = self.sender
        msg['To'] = ', '.join(self.recipients)
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
        except Exception as e:
            logging.error(f"Failed to send alert email: {e}")

class AlertManager:
    """Manages alert rules and handlers."""
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.handlers: List[AlertHandler] = []
        self.last_alerts: Dict[str, datetime] = {}
        self.lock = threading.Lock()
        
    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        with self.lock:
            self.rules[rule.name] = rule
            
    def remove_rule(self, rule_name: str) -> None:
        """Remove an alert rule."""
        with self.lock:
            self.rules.pop(rule_name, None)
            
    def add_handler(self, handler: AlertHandler) -> None:
        """Add an alert handler."""
        with self.lock:
            self.handlers.append(handler)
            
    def check_conditions(
        self,
        metrics: Dict[str, Any],
        query_id: Optional[str] = None
    ) -> None:
        """Check all rules against metrics."""
        now = datetime.now()
        
        with self.lock:
            for rule_name, rule in self.rules.items():
                # Check cooldown
                last_alert = self.last_alerts.get(rule_name)
                if last_alert and now - last_alert < rule.cooldown:
                    continue
                    
                # Check condition
                try:
                    if rule.condition(metrics):
                        # Create alert
                        alert = Alert(
                            rule_name=rule_name,
                            message=rule.message_template.format(**metrics),
                            severity=rule.severity,
                            timestamp=now,
                            context=metrics,
                            query_id=query_id
                        )
                        
                        # Update last alert time
                        self.last_alerts[rule_name] = now
                        
                        # Handle alert
                        self._handle_alert(alert)
                except Exception as e:
                    logging.error(
                        f"Error checking rule {rule_name}: {e}",
                        exc_info=True
                    )
                    
    def _handle_alert(self, alert: Alert) -> None:
        """Process alert through all handlers."""
        for handler in self.handlers:
            try:
                handler.handle_alert(alert)
            except Exception as e:
                logging.error(
                    f"Error in alert handler {handler.__class__.__name__}: {e}",
                    exc_info=True
                )

# Predefined alert rules
def create_default_rules() -> List[AlertRule]:
    """Create default alert rules."""
    return [
        AlertRule(
            name="high_execution_time",
            condition=lambda m: m.get('execution_time_ms', 0) > 5000,
            message_template="Query execution time exceeded 5s: {execution_time_ms}ms",
            severity=AlertSeverity.WARNING
        ),
        AlertRule(
            name="memory_usage",
            condition=lambda m: m.get('memory_usage_mb', 0) > 1000,
            message_template="High memory usage: {memory_usage_mb}MB",
            severity=AlertSeverity.WARNING
        ),
        AlertRule(
            name="error_rate",
            condition=lambda m: len(m.get('errors', [])) > 0,
            message_template="Query errors detected: {errors}",
            severity=AlertSeverity.ERROR
        ),
        AlertRule(
            name="source_timeout",
            condition=lambda m: any(
                s.get('execution_time_ms', 0) > 10000
                for s in m.get('source_metrics', {}).values()
            ),
            message_template="Data source timeout detected",
            severity=AlertSeverity.ERROR
        ),
        AlertRule(
            name="merge_failure",
            condition=lambda m: m.get('merge_metrics', {}).get('error') is not None,
            message_template="Result merge operation failed",
            severity=AlertSeverity.CRITICAL
        )
    ] 