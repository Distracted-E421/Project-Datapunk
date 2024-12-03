from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Union
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    EXPIRED = "expired"

@dataclass
class AlertRule:
    name: str
    description: str
    severity: AlertSeverity
    condition: Callable[[Any], bool]
    check_interval: timedelta
    timeout: timedelta
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Alert:
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_time: Optional[datetime] = None

class NotificationChannel(ABC):
    @abstractmethod
    async def send_notification(self, alert: Alert) -> bool:
        """Send notification for an alert. Returns True if successful."""
        pass

class EmailNotificationChannel(NotificationChannel):
    async def send_notification(self, alert: Alert) -> bool:
        # TODO: Implement email notification
        logger.info(f"Email notification sent for alert: {alert.rule_name}")
        return True

class SlackNotificationChannel(NotificationChannel):
    async def send_notification(self, alert: Alert) -> bool:
        # TODO: Implement Slack notification
        logger.info(f"Slack notification sent for alert: {alert.rule_name}")
        return True

class AlertManager:
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.notification_channels: Dict[AlertSeverity, List[NotificationChannel]] = {
            severity: [] for severity in AlertSeverity
        }
        self._running = False
        self._check_tasks: Dict[str, asyncio.Task] = {}

    def add_rule(self, rule: AlertRule) -> None:
        """Add a new alert rule."""
        if rule.name in self.rules:
            raise ValueError(f"Alert rule '{rule.name}' already exists")
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_name: str) -> None:
        """Remove an alert rule."""
        if rule_name in self._check_tasks:
            self._check_tasks[rule_name].cancel()
            del self._check_tasks[rule_name]
        
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")

    def add_notification_channel(self, severity: Union[AlertSeverity, List[AlertSeverity]], 
                               channel: NotificationChannel) -> None:
        """Add a notification channel for specified severity levels."""
        if isinstance(severity, AlertSeverity):
            severity = [severity]
        
        for sev in severity:
            if channel not in self.notification_channels[sev]:
                self.notification_channels[sev].append(channel)

    def remove_notification_channel(self, severity: Union[AlertSeverity, List[AlertSeverity]], 
                                  channel: NotificationChannel) -> None:
        """Remove a notification channel from specified severity levels."""
        if isinstance(severity, AlertSeverity):
            severity = [severity]
        
        for sev in severity:
            if channel in self.notification_channels[sev]:
                self.notification_channels[sev].remove(channel)

    async def _check_rule(self, rule: AlertRule) -> None:
        """Check a rule's condition and generate alerts if needed."""
        while self._running:
            try:
                result = await asyncio.wait_for(
                    asyncio.coroutine(rule.condition)(),
                    timeout=rule.timeout.total_seconds()
                )
                
                if result:
                    await self._generate_alert(rule)
                elif rule.name in self.active_alerts:
                    await self._resolve_alert(rule.name, "Condition no longer met")
            
            except asyncio.TimeoutError:
                logger.error(f"Alert rule check timed out: {rule.name}")
            except Exception as e:
                logger.error(f"Error checking alert rule {rule.name}: {e}")
            
            await asyncio.sleep(rule.check_interval.total_seconds())

    async def _generate_alert(self, rule: AlertRule) -> None:
        """Generate a new alert from a rule."""
        if rule.name not in self.active_alerts:
            alert = Alert(
                rule_name=rule.name,
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                message=rule.description,
                timestamp=datetime.now(),
                details=rule.metadata
            )
            
            self.active_alerts[rule.name] = alert
            await self._send_notifications(alert)
            logger.info(f"Generated new alert: {rule.name}")

    async def _send_notifications(self, alert: Alert) -> None:
        """Send notifications for an alert through appropriate channels."""
        channels = self.notification_channels[alert.severity]
        
        notification_tasks = [
            channel.send_notification(alert)
            for channel in channels
        ]
        
        if notification_tasks:
            results = await asyncio.gather(*notification_tasks, return_exceptions=True)
            failed = sum(1 for r in results if not isinstance(r, bool) or not r)
            if failed:
                logger.error(f"{failed} notification(s) failed for alert {alert.rule_name}")

    async def start(self) -> None:
        """Start monitoring all alert rules."""
        if self._running:
            return

        self._running = True
        
        for rule in self.rules.values():
            if rule.name not in self._check_tasks:
                self._check_tasks[rule.name] = asyncio.create_task(
                    self._check_rule(rule)
                )

    async def stop(self) -> None:
        """Stop monitoring all alert rules."""
        self._running = False
        
        for task in self._check_tasks.values():
            task.cancel()
        
        if self._check_tasks:
            await asyncio.gather(*self._check_tasks.values(), return_exceptions=True)
        
        self._check_tasks.clear()

    async def acknowledge_alert(self, rule_name: str, acknowledged_by: str) -> None:
        """Acknowledge an active alert."""
        if rule_name not in self.active_alerts:
            raise ValueError(f"No active alert found for rule: {rule_name}")
        
        alert = self.active_alerts[rule_name]
        if alert.status != AlertStatus.ACTIVE:
            raise ValueError(f"Alert {rule_name} is not in ACTIVE status")
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        logger.info(f"Alert {rule_name} acknowledged by {acknowledged_by}")

    async def resolve_alert(self, rule_name: str, resolved_by: str, 
                          resolution_message: Optional[str] = None) -> None:
        """Resolve an active or acknowledged alert."""
        await self._resolve_alert(rule_name, resolution_message, resolved_by)

    async def _resolve_alert(self, rule_name: str, resolution_message: Optional[str] = None,
                           resolved_by: Optional[str] = None) -> None:
        """Internal method to resolve an alert."""
        if rule_name not in self.active_alerts:
            return
        
        alert = self.active_alerts[rule_name]
        if alert.status in (AlertStatus.RESOLVED, AlertStatus.EXPIRED):
            return
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_by = resolved_by
        alert.resolution_time = datetime.now()
        
        if resolution_message:
            if alert.details is None:
                alert.details = {}
            alert.details["resolution_message"] = resolution_message
        
        logger.info(f"Alert {rule_name} resolved by {resolved_by or 'system'}")
        del self.active_alerts[rule_name]

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get all active alerts, optionally filtered by severity."""
        alerts = list(self.active_alerts.values())
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts

    def get_alert(self, rule_name: str) -> Optional[Alert]:
        """Get the current alert for a rule if it exists."""
        return self.active_alerts.get(rule_name) 