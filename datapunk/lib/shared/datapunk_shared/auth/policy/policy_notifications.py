from typing import Dict, List, Optional, Any
import structlog
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from .policy_approval import ApprovalRequest, ApprovalLevel, ApprovalStatus

logger = structlog.get_logger()

class NotificationChannel(Enum):
    """Available notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"

@dataclass
class NotificationConfig:
    """Configuration for notifications."""
    channels: Dict[ApprovalLevel, List[NotificationChannel]]
    templates: Dict[str, str]
    urgent_threshold: int = 4  # hours until expiry
    reminder_interval: int = 24  # hours between reminders

class NotificationManager:
    """Manages approval-related notifications."""
    
    def __init__(self,
                 config: NotificationConfig,
                 email_client=None,
                 slack_client=None,
                 webhook_client=None,
                 sms_client=None):
        self.config = config
        self.email = email_client
        self.slack = slack_client
        self.webhook = webhook_client
        self.sms = sms_client
        self.logger = logger.bind(component="policy_notifications")
    
    async def notify_approvers(self,
                             request: ApprovalRequest,
                             is_urgent: bool = False) -> None:
        """Send notifications to appropriate approvers."""
        try:
            channels = self.config.channels.get(request.required_level, [])
            
            for channel in channels:
                await self._send_notification(
                    channel=channel,
                    template="approval_request",
                    request=request,
                    is_urgent=is_urgent
                )
            
            self.logger.info("approvers_notified",
                           request_id=request.request_id,
                           channels=channels)
            
        except Exception as e:
            self.logger.error("notification_failed",
                            error=str(e))
            raise
    
    async def notify_requestor(self,
                             request: ApprovalRequest,
                             status: ApprovalStatus,
                             reason: Optional[str] = None) -> None:
        """Notify requestor of approval status change."""
        try:
            await self._send_notification(
                channel=NotificationChannel.EMAIL,
                template="request_status",
                request=request,
                status=status,
                reason=reason
            )
            
            self.logger.info("requestor_notified",
                           request_id=request.request_id,
                           status=status.value)
            
        except Exception as e:
            self.logger.error("requestor_notification_failed",
                            error=str(e))
            raise
    
    async def send_reminder(self, request: ApprovalRequest) -> None:
        """Send reminder for pending approval request."""
        try:
            channels = self.config.channels.get(request.required_level, [])
            
            for channel in channels:
                await self._send_notification(
                    channel=channel,
                    template="approval_reminder",
                    request=request,
                    time_remaining=request.expires_at - datetime.utcnow()
                )
            
            self.logger.info("reminder_sent",
                           request_id=request.request_id)
            
        except Exception as e:
            self.logger.error("reminder_failed",
                            error=str(e))
            raise
    
    async def _send_notification(self,
                               channel: NotificationChannel,
                               template: str,
                               **kwargs) -> None:
        """Send notification through specified channel."""
        try:
            message = self._format_message(template, **kwargs)
            
            if channel == NotificationChannel.EMAIL and self.email:
                await self.email.send(message)
            elif channel == NotificationChannel.SLACK and self.slack:
                await self.slack.post(message)
            elif channel == NotificationChannel.WEBHOOK and self.webhook:
                await self.webhook.send(message)
            elif channel == NotificationChannel.SMS and self.sms:
                await self.sms.send(message)
            
        except Exception as e:
            self.logger.error("channel_send_failed",
                            channel=channel.value,
                            error=str(e))
            raise
    
    def _format_message(self, template: str, **kwargs) -> Dict:
        """Format notification message using template."""
        template_str = self.config.templates.get(template)
        if not template_str:
            raise ValueError(f"Template {template} not found")
            
        # Basic template formatting
        message = template_str.format(**kwargs)
        
        return {
            "subject": f"Policy Approval - {template}",
            "body": message,
            "metadata": kwargs
        } 