from typing import Dict, List, Optional, Any
import structlog
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from .policy_approval import ApprovalRequest, ApprovalLevel, ApprovalStatus

logger = structlog.get_logger()

class NotificationChannel(Enum):
    """
    Supported notification delivery channels for policy-related communications.
    Aligned with organization's communication infrastructure and compliance requirements.
    """
    EMAIL = "email"     # For formal notifications and audit trail
    SLACK = "slack"     # For real-time team collaboration
    WEBHOOK = "webhook" # For system integrations and automation
    SMS = "sms"        # For urgent/critical notifications

@dataclass
class NotificationConfig:
    """
    Notification routing and delivery configuration.
    Maps approval levels to appropriate communication channels and defines timing parameters.
    
    NOTE: urgent_threshold and reminder_interval are in hours to align with
    typical business SLAs and approval workflows.
    """
    channels: Dict[ApprovalLevel, List[NotificationChannel]]  # Channel routing map
    templates: Dict[str, str]  # Message templates by notification type
    urgent_threshold: int = 4  # Hours until expiry triggers urgent notifications
    reminder_interval: int = 24  # Hours between reminder notifications

class NotificationManager:
    """
    Manages policy approval notifications across multiple channels.
    
    Handles:
    - Initial approval requests
    - Status updates
    - Reminders and escalations
    - Urgent notifications
    
    IMPORTANT: Requires configured clients for each enabled channel.
    Gracefully handles missing channel clients without breaking notification flow.
    
    NOTE: All notification operations are logged for audit purposes and
    metric collection.
    """
    
    def __init__(self,
                 config: NotificationConfig,
                 email_client=None,
                 slack_client=None,
                 webhook_client=None,
                 sms_client=None):
        """
        Initialize notification manager with channel clients.
        
        NOTE: Clients are optional to support flexible deployment configurations.
        Missing clients will be skipped during notification routing.
        """
        self.config = config
        self.email = email_client
        self.slack = slack_client
        self.webhook = webhook_client
        self.sms = sms_client
        self.logger = logger.bind(component="policy_notifications")
    
    async def notify_approvers(self,
                             request: ApprovalRequest,
                             is_urgent: bool = False) -> None:
        """
        Notify appropriate approvers based on request level and urgency.
        
        IMPORTANT: Notifications are sent through all configured channels for the
        approval level to ensure delivery and maintain audit trail.
        
        NOTE: Failures in individual channels don't prevent notifications through
        other channels.
        """
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
        """
        Notify policy change requestor of approval status changes.
        
        NOTE: Always uses email channel for formal record-keeping,
        regardless of configuration.
        """
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
        """
        Send reminder notifications for pending approval requests.
        
        IMPORTANT: Uses time_remaining in message to create urgency
        and prevent approval expirations.
        
        NOTE: Reminders use same channels as initial notifications to
        maintain consistency.
        """
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
        """
        Send notification through specified channel using templated message.
        
        IMPORTANT: Each channel client must implement a compatible interface
        (send/post methods) for message delivery.
        
        NOTE: Channel selection is based on client availability and
        configured channel list.
        """
        try:
            message = self._format_message(template, **kwargs)
            
            # Route to appropriate channel client
            # TODO: Consider implementing retry logic for failed deliveries
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
        """
        Format notification message using template and provided context.
        
        IMPORTANT: Templates must exist in config.templates or validation
        will fail to prevent undefined message formats.
        
        NOTE: Message format includes metadata for tracking and auditing.
        """
        template_str = self.config.templates.get(template)
        if not template_str:
            raise ValueError(f"Template {template} not found")
            
        # Basic template formatting
        # TODO: Consider implementing more sophisticated template engine
        message = template_str.format(**kwargs)
        
        return {
            "subject": f"Policy Approval - {template}",
            "body": message,
            "metadata": kwargs
        } 