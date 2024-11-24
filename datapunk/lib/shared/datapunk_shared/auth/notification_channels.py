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
    """Priority levels for notifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class NotificationTemplate:
    """Template for notification content."""
    subject: str
    body: str
    format: str = "text"  # text, html, markdown
    variables: Dict[str, str] = None

class BaseNotificationChannel:
    """Base class for notification channels."""
    
    async def send(self,
                  message: Dict[str, Any],
                  priority: NotificationPriority) -> bool:
        """Send notification through channel."""
        raise NotImplementedError

class SlackNotifier(BaseNotificationChannel):
    """Slack notification channel."""
    
    def __init__(self, webhook_url: str, default_channel: str):
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
        """Format message as Slack blocks."""
        color_map = {
            NotificationPriority.LOW: "#36a64f",
            NotificationPriority.MEDIUM: "#ECB22E",
            NotificationPriority.HIGH: "#E01E5A",
            NotificationPriority.URGENT: "#FF0000"
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
    """Microsoft Teams notification channel."""
    
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
        """Create Teams Adaptive Card."""
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
    """SMS notification channel."""
    
    def __init__(self, twilio_client):
        self.client = twilio_client
        self.logger = logger.bind(channel="sms")
    
    async def send(self,
                  message: Dict[str, Any],
                  priority: NotificationPriority = NotificationPriority.MEDIUM) -> bool:
        """Send SMS notification."""
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
    """PagerDuty notification channel."""
    
    def __init__(self, api_key: str, service_id: str):
        self.api_key = api_key
        self.service_id = service_id
        self.logger = logger.bind(channel="pagerduty")
    
    async def send(self,
                  message: Dict[str, Any],
                  priority: NotificationPriority = NotificationPriority.MEDIUM) -> bool:
        """Create PagerDuty incident."""
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