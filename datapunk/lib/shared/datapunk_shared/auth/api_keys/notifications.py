from typing import Dict, Optional, TYPE_CHECKING, Set
import structlog
from enum import Enum, auto
from datetime import datetime
import asyncio
from dataclasses import dataclass

if TYPE_CHECKING:
    from ....messaging import MessageBroker
    from ....monitoring import MetricsClient

logger = structlog.get_logger()

class KeyEventType(Enum):
    """Types of API key events."""
    CREATED = "created"
    ROTATED = "rotated"
    EXPIRED = "expired"
    REVOKED = "revoked"
    COMPROMISED = "compromised"
    NEAR_EXPIRY = "near_expiry"
    POLICY_UPDATED = "policy_updated"

class NotificationChannel(Enum):
    """Available notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    METRICS = "metrics"
    AUDIT_LOG = "audit_log"
    SECURITY_ALERT = "security_alert"
    ADMIN_DASHBOARD = "admin_dashboard"

class NotificationPriority(Enum):
    """Priority levels for notifications."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    channels: Set[NotificationChannel]
    priority_channels: Dict[NotificationPriority, Set[NotificationChannel]]
    alert_thresholds: Dict[str, int]
    retry_attempts: int = 3
    retry_delay: int = 5  # seconds

class KeyNotifier:
    """Handles notifications for API key events."""
    
    def __init__(self,
                 message_broker: 'MessageBroker',
                 metrics: 'MetricsClient',
                 config: NotificationConfig):
        self.broker = message_broker
        self.metrics = metrics
        self.config = config
        self.logger = logger.bind(component="key_notifier")
    
    async def notify(self,
                    event_type: KeyEventType,
                    key_id: str,
                    service: str,
                    details: Optional[Dict] = None) -> None:
        """Send notification for key event."""
        try:
            event = {
                "event_type": event_type.value,
                "key_id": key_id,
                "service": service,
                "timestamp": datetime.utcnow().isoformat(),
                "details": details or {}
            }
            
            # Send to appropriate channels based on event type
            await self._route_notification(event)
            
            # Update metrics
            self.metrics.increment(
                "key_notifications_sent",
                {"event_type": event_type.value}
            )
            
        except Exception as e:
            self.logger.error("notification_failed",
                            event_type=event_type.value,
                            error=str(e))
            self.metrics.increment("notification_errors")
    
    async def _route_notification(self, event: Dict) -> None:
        """Route notification to appropriate channels."""
        try:
            priority = self._determine_priority(event)
            channels = self._get_channels(priority)
            
            for channel in channels:
                await self._send_to_channel(channel, event, priority)
            
            # Archive all events
            await self.broker.publish(
                "key_events.archive",
                event
            )
            
        except Exception as e:
            self.logger.error("notification_routing_failed",
                            error=str(e))
            raise
    
    def _determine_priority(self, event: Dict) -> NotificationPriority:
        """Determine notification priority based on event type."""
        event_type = event["event_type"]
        
        if event_type in {"compromised", "security_breach"}:
            return NotificationPriority.CRITICAL
        elif event_type in {"revoked", "policy_violation"}:
            return NotificationPriority.HIGH
        elif event_type in {"near_expiry", "policy_updated"}:
            return NotificationPriority.MEDIUM
        return NotificationPriority.LOW
    
    def _get_channels(self, priority: NotificationPriority) -> Set[NotificationChannel]:
        """Get appropriate channels for priority level."""
        channels = set()
        
        # Add priority-specific channels
        if priority in self.config.priority_channels:
            channels.update(self.config.priority_channels[priority])
        
        # Add default channels
        channels.update(self.config.channels)
        
        return channels
    
    async def _send_to_channel(self,
                              channel: NotificationChannel,
                              event: Dict,
                              priority: NotificationPriority) -> None:
        """Send notification to specific channel with retry logic."""
        attempts = 0
        while attempts < self.config.retry_attempts:
            try:
                if channel == NotificationChannel.EMAIL:
                    await self._send_email(event, priority)
                elif channel == NotificationChannel.SLACK:
                    await self._send_slack(event, priority)
                elif channel == NotificationChannel.WEBHOOK:
                    await self._send_webhook(event, priority)
                elif channel == NotificationChannel.SECURITY_ALERT:
                    await self._send_security_alert(event, priority)
                
                # Update metrics
                self.metrics.increment(
                    "notifications_sent",
                    {
                        "channel": channel.value,
                        "priority": priority.value,
                        "success": "true"
                    }
                )
                return
                
            except Exception as e:
                attempts += 1
                if attempts == self.config.retry_attempts:
                    self.logger.error("notification_failed",
                                    channel=channel.value,
                                    error=str(e))
                    self.metrics.increment(
                        "notification_failures",
                        {"channel": channel.value}
                    )
                else:
                    await asyncio.sleep(self.config.retry_delay)
    
    async def _send_email(self, event: Dict, priority: NotificationPriority) -> None:
        """Send email notification."""
        template = self._get_email_template(event["event_type"])
        recipients = self._get_recipients(priority)
        
        # Email sending implementation
        pass
    
    async def _send_slack(self, event: Dict, priority: NotificationPriority) -> None:
        """Send Slack notification."""
        channel = self._get_slack_channel(priority)
        message = self._format_slack_message(event)
        
        # Slack sending implementation
        pass
    
    async def _send_webhook(self, event: Dict, priority: NotificationPriority) -> None:
        """Send webhook notification."""
        endpoints = self._get_webhook_endpoints(priority)
        
        # Webhook sending implementation
        pass
    
    async def _send_security_alert(self, event: Dict, priority: NotificationPriority) -> None:
        """Send security alert."""
        if priority >= NotificationPriority.HIGH:
            await self.broker.publish(
                "security.alerts.high_priority",
                {
                    **event,
                    "alert_level": priority.value,
                    "requires_immediate_action": True
                }
            ) 