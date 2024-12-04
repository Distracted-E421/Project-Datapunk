"""
API Key Notification Tests
------------------------

Tests the notification system for API key events including:
- Event dispatching
- Channel configuration
- Priority handling
- Error recovery
- Rate limiting

Run with: pytest -v test_notifications.py
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from datapunk_shared.auth.api_keys import (
    KeyNotifier, KeyEventType, NotificationChannel,
    NotificationPriority, NotificationConfig
)

# Test Fixtures

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    return client

@pytest.fixture
def message_broker():
    """Mock message broker for notifications."""
    broker = AsyncMock()
    broker.publish = AsyncMock()
    return broker

@pytest.fixture
def notification_config():
    """Create test notification configuration."""
    return NotificationConfig(
        channels={
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK,
            NotificationChannel.WEBHOOK
        },
        rate_limit=100,
        batch_size=10,
        retry_attempts=3
    )

@pytest.fixture
def key_notifier(metrics_client, message_broker, notification_config):
    """Create key notifier instance for testing."""
    return KeyNotifier(
        metrics=metrics_client,
        broker=message_broker,
        config=notification_config
    )

# Event Notification Tests

@pytest.mark.asyncio
async def test_notify_key_creation(key_notifier):
    """Test notification for key creation event."""
    await key_notifier.notify(
        event_type=KeyEventType.CREATED,
        key_id="test_key",
        service="test_service",
        metadata={"created_by": "test_user"}
    )
    
    # Verify message published
    key_notifier.broker.publish.assert_called_once()
    
    # Verify metrics
    key_notifier.metrics.increment.assert_called_with(
        "key_notifications",
        {
            "event": KeyEventType.CREATED.value,
            "service": "test_service"
        }
    )

@pytest.mark.asyncio
async def test_notify_key_rotation(key_notifier):
    """Test notification for key rotation event."""
    metadata = {
        "reason": "age",
        "rotated_by": "test_user",
        "overlap_ends_at": datetime.utcnow().isoformat()
    }
    
    await key_notifier.notify(
        event_type=KeyEventType.ROTATED,
        key_id="test_key",
        service="test_service",
        metadata=metadata
    )
    
    # Verify high priority for rotation events
    call_args = key_notifier.broker.publish.call_args[0]
    assert call_args[1]["priority"] == NotificationPriority.HIGH

@pytest.mark.asyncio
async def test_notify_emergency_rotation(key_notifier):
    """Test notification for emergency rotation event."""
    metadata = {
        "reason": "security_incident",
        "rotated_by": "security_team",
        "emergency": True
    }
    
    await key_notifier.notify(
        event_type=KeyEventType.ROTATED,
        key_id="test_key",
        service="test_service",
        metadata=metadata
    )
    
    # Verify critical priority for emergency events
    call_args = key_notifier.broker.publish.call_args[0]
    assert call_args[1]["priority"] == NotificationPriority.CRITICAL

# Channel Configuration Tests

@pytest.mark.asyncio
async def test_channel_filtering(key_notifier):
    """Test notification channel filtering."""
    # Disable Slack channel
    key_notifier.config.channels.remove(NotificationChannel.SLACK)
    
    await key_notifier.notify(
        event_type=KeyEventType.CREATED,
        key_id="test_key",
        service="test_service"
    )
    
    # Verify channel selection
    call_args = key_notifier.broker.publish.call_args[0]
    channels = call_args[1]["channels"]
    assert NotificationChannel.EMAIL in channels
    assert NotificationChannel.WEBHOOK in channels
    assert NotificationChannel.SLACK not in channels

@pytest.mark.asyncio
async def test_priority_channel_override(key_notifier):
    """Test channel override for high priority events."""
    # Configure priority channel override
    key_notifier.config.priority_channels = {
        NotificationPriority.CRITICAL: {NotificationChannel.EMAIL}
    }
    
    await key_notifier.notify(
        event_type=KeyEventType.REVOKED,
        key_id="test_key",
        service="test_service",
        metadata={"reason": "security_incident"}
    )
    
    # Verify only email channel used for critical events
    call_args = key_notifier.broker.publish.call_args[0]
    assert call_args[1]["channels"] == {NotificationChannel.EMAIL}

# Error Handling Tests

@pytest.mark.asyncio
async def test_broker_failure_handling(key_notifier):
    """Test graceful handling of broker failures."""
    key_notifier.broker.publish.side_effect = Exception("Broker connection failed")
    
    # Should not raise exception
    await key_notifier.notify(
        event_type=KeyEventType.CREATED,
        key_id="test_key",
        service="test_service"
    )
    
    # Should record error metric
    key_notifier.metrics.increment.assert_called_with(
        "key_notification_errors",
        {"event": KeyEventType.CREATED.value}
    )

@pytest.mark.asyncio
async def test_retry_mechanism(key_notifier):
    """Test notification retry mechanism."""
    # Fail first attempt, succeed on retry
    key_notifier.broker.publish.side_effect = [
        Exception("First attempt failed"),
        None  # Success on second attempt
    ]
    
    await key_notifier.notify(
        event_type=KeyEventType.CREATED,
        key_id="test_key",
        service="test_service"
    )
    
    # Verify retry attempt
    assert key_notifier.broker.publish.call_count == 2

# Rate Limiting Tests

@pytest.mark.asyncio
async def test_rate_limiting(key_notifier):
    """Test notification rate limiting."""
    # Set low rate limit
    key_notifier.config.rate_limit = 2
    
    # Send multiple notifications
    for _ in range(5):
        await key_notifier.notify(
            event_type=KeyEventType.CREATED,
            key_id="test_key",
            service="test_service"
        )
    
    # Verify rate limiting
    assert key_notifier.broker.publish.call_count <= 2
    
    # Verify rate limit metric
    key_notifier.metrics.increment.assert_called_with(
        "key_notifications_rate_limited",
        {"service": "test_service"}
    )

@pytest.mark.asyncio
async def test_batch_processing(key_notifier):
    """Test notification batch processing."""
    # Configure small batch size
    key_notifier.config.batch_size = 2
    
    # Send multiple notifications
    notifications = [
        (KeyEventType.CREATED, "key1"),
        (KeyEventType.UPDATED, "key2"),
        (KeyEventType.ROTATED, "key3")
    ]
    
    for event_type, key_id in notifications:
        await key_notifier.notify(
            event_type=event_type,
            key_id=key_id,
            service="test_service"
        )
    
    # Verify batch processing
    assert key_notifier.broker.publish.call_count == 2  # 2 batches 