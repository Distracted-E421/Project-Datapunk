import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
from datapunk_shared.auth.policy.policy_notifications import (
    NotificationChannel, NotificationConfig, NotificationManager
)
from datapunk_shared.auth.policy.policy_approval import (
    ApprovalRequest, ApprovalLevel, ApprovalStatus
)
from datapunk_shared.auth.policy.types import PolicyValidationResult, RiskLevel

@pytest.fixture
def email_client():
    """Create a mock email client."""
    client = Mock()
    client.send = AsyncMock()
    return client

@pytest.fixture
def slack_client():
    """Create a mock Slack client."""
    client = Mock()
    client.post = AsyncMock()
    return client

@pytest.fixture
def webhook_client():
    """Create a mock webhook client."""
    client = Mock()
    client.send = AsyncMock()
    return client

@pytest.fixture
def sms_client():
    """Create a mock SMS client."""
    client = Mock()
    client.send = AsyncMock()
    return client

@pytest.fixture
def notification_config():
    """Create a sample notification configuration."""
    return NotificationConfig(
        channels={
            ApprovalLevel.TEAM_LEAD: [NotificationChannel.EMAIL, NotificationChannel.SLACK],
            ApprovalLevel.SECURITY: [NotificationChannel.EMAIL, NotificationChannel.SMS]
        },
        templates={
            "approval_request": "New approval request: {request_id}",
            "request_status": "Request {request_id} status: {status}",
            "approval_reminder": "Reminder for request: {request_id}"
        },
        urgent_threshold=4,
        reminder_interval=24
    )

@pytest.fixture
def notification_manager(notification_config, email_client, slack_client, webhook_client, sms_client):
    """Create a NotificationManager instance with mock dependencies."""
    return NotificationManager(
        config=notification_config,
        email_client=email_client,
        slack_client=slack_client,
        webhook_client=webhook_client,
        sms_client=sms_client
    )

@pytest.fixture
def sample_approval_request():
    """Create a sample approval request."""
    return ApprovalRequest(
        request_id="request-001",
        policy_id="policy-001",
        requester_id="user-001",
        validation_result=PolicyValidationResult(
            valid=True,
            issues=[],
            warnings=[],
            risk_level=RiskLevel.MEDIUM,
            breaking_changes=[]
        ),
        required_level=ApprovalLevel.TEAM_LEAD,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7)
    )

def test_notification_channel_enum():
    """Test NotificationChannel enum values."""
    assert NotificationChannel.EMAIL.value == "email"
    assert NotificationChannel.SLACK.value == "slack"
    assert NotificationChannel.WEBHOOK.value == "webhook"
    assert NotificationChannel.SMS.value == "sms"

def test_notification_config_creation():
    """Test NotificationConfig creation and properties."""
    config = NotificationConfig(
        channels={
            ApprovalLevel.TEAM_LEAD: [NotificationChannel.EMAIL]
        },
        templates={"test": "template"},
        urgent_threshold=2,
        reminder_interval=12
    )
    
    assert ApprovalLevel.TEAM_LEAD in config.channels
    assert config.channels[ApprovalLevel.TEAM_LEAD] == [NotificationChannel.EMAIL]
    assert config.templates == {"test": "template"}
    assert config.urgent_threshold == 2
    assert config.reminder_interval == 12

@pytest.mark.asyncio
async def test_notify_approvers_success(notification_manager, sample_approval_request):
    """Test successful notification of approvers."""
    # Execute
    await notification_manager.notify_approvers(sample_approval_request)
    
    # Verify
    notification_manager.email.send.assert_called_once()
    notification_manager.slack.post.assert_called_once()
    notification_manager.sms.send.assert_not_called()

@pytest.mark.asyncio
async def test_notify_approvers_urgent(notification_manager, sample_approval_request):
    """Test urgent notification of approvers."""
    # Execute
    await notification_manager.notify_approvers(sample_approval_request, is_urgent=True)
    
    # Verify
    notification_manager.email.send.assert_called_once()
    notification_manager.slack.post.assert_called_once()

@pytest.mark.asyncio
async def test_notify_requestor_success(notification_manager, sample_approval_request):
    """Test successful notification of requestor."""
    # Execute
    await notification_manager.notify_requestor(
        request=sample_approval_request,
        status=ApprovalStatus.APPROVED,
        reason="Approved by team lead"
    )
    
    # Verify
    notification_manager.email.send.assert_called_once()

@pytest.mark.asyncio
async def test_send_reminder_success(notification_manager, sample_approval_request):
    """Test successful sending of reminder."""
    # Execute
    await notification_manager.send_reminder(sample_approval_request)
    
    # Verify
    notification_manager.email.send.assert_called_once()
    notification_manager.slack.post.assert_called_once()

@pytest.mark.asyncio
async def test_send_notification_email(notification_manager):
    """Test sending notification through email channel."""
    # Execute
    await notification_manager._send_notification(
        channel=NotificationChannel.EMAIL,
        template="approval_request",
        request_id="test-001"
    )
    
    # Verify
    notification_manager.email.send.assert_called_once()

@pytest.mark.asyncio
async def test_send_notification_slack(notification_manager):
    """Test sending notification through Slack channel."""
    # Execute
    await notification_manager._send_notification(
        channel=NotificationChannel.SLACK,
        template="approval_request",
        request_id="test-001"
    )
    
    # Verify
    notification_manager.slack.post.assert_called_once()

@pytest.mark.asyncio
async def test_send_notification_missing_template(notification_manager):
    """Test handling of missing template."""
    # Execute and verify
    with pytest.raises(ValueError, match="Template missing_template not found"):
        await notification_manager._send_notification(
            channel=NotificationChannel.EMAIL,
            template="missing_template",
            request_id="test-001"
        )

@pytest.mark.asyncio
async def test_send_notification_missing_client(notification_manager):
    """Test handling of missing channel client."""
    # Setup
    notification_manager.email = None
    
    # Execute
    await notification_manager._send_notification(
        channel=NotificationChannel.EMAIL,
        template="approval_request",
        request_id="test-001"
    )
    
    # Verify no error is raised and notification is skipped

def test_format_message(notification_manager):
    """Test message formatting with template."""
    # Execute
    message = notification_manager._format_message(
        template="approval_request",
        request_id="test-001"
    )
    
    # Verify
    assert message["subject"] == "Policy Approval - approval_request"
    assert "test-001" in message["body"]
    assert message["metadata"]["request_id"] == "test-001" 