import pytest
import aiohttp
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from datapunk_shared.auth.notification_channels import (
    NotificationPriority,
    NotificationTemplate,
    BaseNotificationChannel,
    SlackNotifier,
    TeamsNotifier,
    SMSNotifier
)

@pytest.fixture
def mock_session():
    """Mock aiohttp ClientSession for testing HTTP requests."""
    with patch("aiohttp.ClientSession") as mock:
        mock.return_value.__aenter__.return_value.post = AsyncMock()
        mock.return_value.__aexit__ = AsyncMock()
        yield mock

@pytest.fixture
def test_message():
    """Sample test message for notifications."""
    return {
        "subject": "Test Alert",
        "body": "This is a test notification"
    }

class TestNotificationPriority:
    def test_priority_values(self):
        """Test priority enum values."""
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.MEDIUM.value == "medium"
        assert NotificationPriority.HIGH.value == "high"
        assert NotificationPriority.URGENT.value == "urgent"

class TestNotificationTemplate:
    def test_template_creation(self):
        """Test template creation with variables."""
        template = NotificationTemplate(
            subject="Alert: ${service}",
            body="Issue detected in ${service} at ${time}",
            format="text",
            variables={"service": "auth", "time": "12:00"}
        )
        assert template.subject == "Alert: ${service}"
        assert template.format == "text"
        assert "service" in template.variables

class TestSlackNotifier:
    @pytest.fixture
    def slack_notifier(self):
        return SlackNotifier("https://hooks.slack.com/test", "#alerts")

    @pytest.mark.asyncio
    async def test_successful_notification(self, slack_notifier, mock_session, test_message):
        """Test successful Slack notification."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

        result = await slack_notifier.send(test_message, NotificationPriority.HIGH)
        assert result is True

    @pytest.mark.asyncio
    async def test_failed_notification(self, slack_notifier, mock_session, test_message):
        """Test failed Slack notification."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

        result = await slack_notifier.send(test_message, NotificationPriority.HIGH)
        assert result is False

    def test_block_formatting(self, slack_notifier, test_message):
        """Test Slack message block formatting."""
        blocks = slack_notifier._format_blocks(test_message, NotificationPriority.HIGH)
        assert len(blocks) == 3
        assert blocks[0]["type"] == "header"
        assert blocks[1]["type"] == "section"
        assert blocks[2]["type"] == "context"

class TestTeamsNotifier:
    @pytest.fixture
    def teams_notifier(self):
        return TeamsNotifier("https://teams.webhook.office.com/test")

    @pytest.mark.asyncio
    async def test_successful_notification(self, teams_notifier, mock_session, test_message):
        """Test successful Teams notification."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

        result = await teams_notifier.send(test_message, NotificationPriority.MEDIUM)
        assert result is True

    @pytest.mark.asyncio
    async def test_failed_notification(self, teams_notifier, mock_session, test_message):
        """Test failed Teams notification."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

        result = await teams_notifier.send(test_message, NotificationPriority.MEDIUM)
        assert result is False

    def test_adaptive_card_creation(self, teams_notifier, test_message):
        """Test Teams Adaptive Card creation."""
        card = teams_notifier._create_adaptive_card(test_message, NotificationPriority.MEDIUM)
        assert card["contentType"] == "application/vnd.microsoft.card.adaptive"
        assert card["content"]["type"] == "AdaptiveCard"
        assert card["content"]["version"] == "1.2"

class TestSMSNotifier:
    @pytest.fixture
    def mock_twilio_client(self):
        return Mock()

    @pytest.fixture
    def sms_notifier(self, mock_twilio_client):
        return SMSNotifier(mock_twilio_client)

    @pytest.mark.asyncio
    async def test_send_sms(self, sms_notifier, test_message):
        """Test SMS sending with Twilio client."""
        sms_notifier.client.messages.create = AsyncMock(return_value=Mock(sid="test_sid"))
        
        result = await sms_notifier.send(test_message, NotificationPriority.URGENT)
        assert result is True

    @pytest.mark.asyncio
    async def test_sms_failure(self, sms_notifier, test_message):
        """Test SMS failure handling."""
        sms_notifier.client.messages.create = AsyncMock(side_effect=Exception("Failed to send"))
        
        result = await sms_notifier.send(test_message, NotificationPriority.URGENT)
        assert result is False 