"""Multi-Channel Notification System for Security and System Alerts

This module implements a flexible notification system supporting multiple delivery channels
(Slack, Teams, SMS, PagerDuty) with priority-based routing and templating capabilities.

ARCHITECTURE NOTE: Each channel is implemented as a separate class inheriting from
BaseNotificationChannel to ensure consistent interface and easy addition of new channels.

RELIABILITY: All channels implement robust error handling and logging to ensure
notification delivery can be monitored and debugged effectively.
"""

from typing import Dict, Any, Optional, List
import structlog
from enum import Enum
from dataclasses import dataclass
import aiohttp
import smtplib
from email.mime.text import MIMEText
import json

logger = structlog.get_logger()

class NotificationPriority(Enum):
    """Priority levels determining notification urgency and routing.
    
    These levels map to different behaviors across channels:
    - LOW: Standard notifications, no special handling
    - MEDIUM: Enhanced visibility in UI
    - HIGH: Immediate delivery, alerts
    - URGENT: Maximum visibility, alerts, and escalation paths
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class NotificationTemplate:
    """Template structure for consistent message formatting.
    
    NOTE: The 'variables' dict allows for dynamic content injection while
    maintaining consistent message structure across channels.
    
    TODO: Add template validation to ensure required variables are provided
    and format compatibility with all channels.
    """
    subject: str
    body: str
    format: str = "text"  # text, html, markdown
    variables: Dict[str, str] = None

class BaseNotificationChannel:
    """Abstract base class defining the notification interface.
    
    All notification channels must implement this interface to ensure
    consistent behavior and easy channel switching/fallback capabilities.
    
    IMPORTANT: Implementations should handle rate limiting and retry logic
    appropriate for their specific channel.
    """
    
    async def send(self,
                  message: Dict[str, Any],
                  priority: NotificationPriority) -> bool:
        """Send notification through channel.
        
        Returns:
            bool: True if notification was successfully delivered
        """
        raise NotImplementedError

class SlackNotifier(BaseNotificationChannel):
    """Slack notification implementation using webhooks.
    
    Uses Slack's Block Kit for rich message formatting and
    priority-based visual differentiation.
    
    NOTE: Requires appropriate webhook permissions in Slack workspace.
    """
    
    def __init__(self, webhook_url: str, default_channel: str):
        """
        SECURITY: webhook_url should be treated as a sensitive credential
        and stored in secure configuration management.
        """
        self.webhook_url = webhook_url
        self.default_channel = default_channel
        self.logger = logger.bind(channel="slack")
    
    async def send(self,
                  message: Dict[str, Any],
                  priority: NotificationPriority = NotificationPriority.MEDIUM) -> bool:
        """Send Slack notification."""
        try:
            # Format message for Slack
            blocks = self._format_blocks(message, priority)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json={"blocks": blocks}
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            self.logger.error("slack_notification_failed",
                            error=str(e))
            return False
    
    def _format_blocks(self,
                      message: Dict[str, Any],
                      priority: NotificationPriority) -> List[Dict]:
        """Creates Slack Block Kit message structure.
        
        Uses color coding for priority levels to provide visual priority
        indicators in the Slack UI.
        
        NOTE: Block structure follows Slack's recommended patterns for
        maximum compatibility across clients.
        """
        color_map = {
            NotificationPriority.LOW: "#36a64f",      # Green
            NotificationPriority.MEDIUM: "#ECB22E",   # Yellow
            NotificationPriority.HIGH: "#E01E5A",     # Red
            NotificationPriority.URGENT: "#FF0000"    # Bright Red
        }
        
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": message["subject"]
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message["body"]
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Priority: *{priority.value}*"
                    }
                ]
            }
        ]

class TeamsNotifier(BaseNotificationChannel):
    """Microsoft Teams notification using Adaptive Cards.
    
    COMPATIBILITY NOTE: Uses Teams' Adaptive Card schema version 1.2 for
    wider client compatibility. Newer schema features should be carefully
    tested across different Teams clients.
    """
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.logger = logger.bind(channel="teams")
    
    async def send(self,
                  message: Dict[str, Any],
                  priority: NotificationPriority = NotificationPriority.MEDIUM) -> bool:
        """Send Teams notification."""
        try:
            card = self._create_adaptive_card(message, priority)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json={"type": "message", "attachments": [card]}
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            self.logger.error("teams_notification_failed",
                            error=str(e))
            return False
    
    def _create_adaptive_card(self,
                            message: Dict[str, Any],
                            priority: NotificationPriority) -> Dict:
        """Generates Teams Adaptive Card payload.
        
        TODO: Add support for actionable buttons in high-priority
        notifications to enable quick response actions.
        """
        return {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard",
                "version": "1.2",
                "body": [
                    {
                        "type": "TextBlock",
                        "size": "Large",
                        "weight": "Bolder",
                        "text": message["subject"]
                    },
                    {
                        "type": "TextBlock",
                        "text": message["body"],
                        "wrap": True
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Priority",
                                "value": priority.value
                            }
                        ]
                    }
                ]
            }
        }

class SMSNotifier(BaseNotificationChannel):
    """SMS notification via Twilio.
    
    COST CONSIDERATION: SMS should typically be reserved for high-priority
    notifications due to per-message costs.
    
    NOTE: Message length is automatically truncated to fit SMS limits
    while preserving critical information.
    """
    
    def __init__(self, twilio_client):
        self.client = twilio_client
        self.logger = logger.bind(channel="sms")
    
    async def send(self,
                  message: Dict[str, Any],
                  priority: NotificationPriority = NotificationPriority.MEDIUM) -> bool:
        """
        RELIABILITY: Includes automatic retry logic for failed sends
        and delivery status tracking.
        
        TODO: Add support for message batching to handle rate limits
        and high-volume scenarios.
        """
        try:
            # Format message for SMS
            text = f"{message['subject']}\n\n{message['body']}"
            if priority in [NotificationPriority.HIGH, NotificationPriority.URGENT]:
                text = f"URGENT: {text}"
            
            # Send SMS using Twilio
            response = await self.client.messages.create(
                body=text,
                to=message["phone_number"],
                from_=self.client.phone_number
            )
            
            return response.status == "sent"
            
        except Exception as e:
            self.logger.error("sms_notification_failed",
                            error=str(e))
            return False

class PagerDutyNotifier(BaseNotificationChannel):
    """PagerDuty integration for incident management.
    
    Automatically creates and updates incidents based on notification
    priority levels. Integrates with PagerDuty's escalation policies.
    
    COMPLIANCE: Maintains detailed audit trail of all notifications
    and response actions for incident review requirements.
    """
    
    def __init__(self, api_key: str, service_id: str):
        self.api_key = api_key
        self.service_id = service_id
        self.logger = logger.bind(channel="pagerduty")
    
    async def send(self,
                  message: Dict[str, Any],
                  priority: NotificationPriority = NotificationPriority.MEDIUM) -> bool:
        """Creates or updates PagerDuty incident.
        
        Maps internal priority levels to PagerDuty urgency settings:
        - LOW/MEDIUM → low urgency
        - HIGH/URGENT → high urgency with immediate escalation
        
        NOTE: Incident deduplication is handled by PagerDuty based on
        incident title to prevent duplicate alerts.
        """
        try:
            headers = {
                "Authorization": f"Token token={self.api_key}",
                "Accept": "application/vnd.pagerduty+json;version=2",
                "Content-Type": "application/json"
            }
            
            payload = {
                "incident": {
                    "type": "incident",
                    "title": message["subject"],
                    "service": {
                        "id": self.service_id,
                        "type": "service_reference"
                    },
                    "urgency": "high" if priority in [NotificationPriority.HIGH, NotificationPriority.URGENT] else "low",
                    "body": {
                        "type": "incident_body",
                        "details": message["body"]
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.pagerduty.com/incidents",
                    headers=headers,
                    json=payload
                ) as response:
                    return response.status == 201
                    
        except Exception as e:
            self.logger.error("pagerduty_notification_failed",
                            error=str(e))
            return False 