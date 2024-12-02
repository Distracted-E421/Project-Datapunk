"""
API Key Rotation Tests
-------------------

Tests the key rotation system including:
- Automated rotation based on age and usage
- Emergency rotation procedures
- Overlap period management
- Service notification coordination
- Audit trail maintenance

Run with: pytest -v test_rotation.py
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from datapunk_shared.auth.api_keys import (
    KeyRotationManager, RotationReason, RotationConfig,
    KeyType, KeyPolicy, KeyNotifier, KeyEventType
)
from datapunk_shared.auth.api_keys.types import KeyID

# Test Fixtures

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.gauge = AsyncMock()
    return client

@pytest.fixture
def key_manager():
    """Mock API key manager."""
    manager = AsyncMock()
    manager.create_key = AsyncMock()
    manager.revoke_key = AsyncMock()
    manager.get_key = AsyncMock()
    return manager

@pytest.fixture
def notifier():
    """Mock key notifier."""
    notifier = AsyncMock()
    notifier.notify = AsyncMock()
    return notifier

@pytest.fixture
def rotation_config():
    """Create rotation configuration for testing."""
    return RotationConfig(
        max_key_age=timedelta(days=90),
        overlap_period=timedelta(hours=24),
        min_rotation_interval=timedelta(days=30),
        emergency_overlap=timedelta(minutes=30)
    )

@pytest.fixture
def rotation_manager(key_manager, metrics_client, notifier, rotation_config):
    """Create rotation manager for testing."""
    return KeyRotationManager(
        key_manager=key_manager,
        metrics=metrics_client,
        notifier=notifier,
        config=rotation_config
    )

# Rotation Check Tests

@pytest.mark.asyncio
async def test_check_rotation_needed_age(rotation_manager, key_manager):
    """Test rotation check based on key age."""
    # Setup old key
    old_key_data = {
        "created_at": (datetime.utcnow() - timedelta(days=100)).isoformat(),
        "service": "test_service",
        "policy": {"type": KeyType.SERVICE.value}
    }
    key_manager.get_key.return_value = old_key_data
    
    result = await rotation_manager.check_rotation_needed("test_key")
    
    assert result["needs_rotation"] is True
    assert "age" in result["reasons"]
    assert result["urgency"] == "normal"

@pytest.mark.asyncio
async def test_check_rotation_needed_usage(rotation_manager, key_manager):
    """Test rotation check based on usage patterns."""
    # Setup heavily used key
    key_data = {
        "created_at": datetime.utcnow().isoformat(),
        "service": "test_service",
        "policy": {"type": KeyType.SERVICE.value},
        "usage": {
            "total_requests": 1000000,
            "unique_ips": 1000,
            "error_rate": 0.05
        }
    }
    key_manager.get_key.return_value = key_data
    
    result = await rotation_manager.check_rotation_needed("test_key")
    
    assert result["needs_rotation"] is True
    assert "usage" in result["reasons"]

@pytest.mark.asyncio
async def test_check_rotation_needed_security(rotation_manager, key_manager):
    """Test rotation check based on security events."""
    # Setup key with security incidents
    key_data = {
        "created_at": datetime.utcnow().isoformat(),
        "service": "test_service",
        "policy": {"type": KeyType.SERVICE.value},
        "security_events": [
            {
                "type": "suspicious_ip",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    }
    key_manager.get_key.return_value = key_data
    
    result = await rotation_manager.check_rotation_needed("test_key")
    
    assert result["needs_rotation"] is True
    assert "security" in result["reasons"]
    assert result["urgency"] == "high"

# Rotation Execution Tests

@pytest.mark.asyncio
async def test_rotate_key_success(rotation_manager, key_manager):
    """Test successful key rotation."""
    # Setup existing key
    old_key_data = {
        "service": "test_service",
        "policy": {
            "type": KeyType.SERVICE.value,
            "rate_limit": 1000
        }
    }
    key_manager.get_key.return_value = old_key_data
    
    # Setup new key
    new_key_data = {
        "key_id": "new_key_id",
        "key": "new_key_secret",
        "service": "test_service"
    }
    key_manager.create_key.return_value = new_key_data
    
    result = await rotation_manager.rotate_key(
        key_id="old_key_id",
        reason=RotationReason.AGE,
        rotated_by="test_user"
    )
    
    assert result["success"] is True
    assert result["new_key"] == new_key_data
    assert "overlap_ends_at" in result

@pytest.mark.asyncio
async def test_emergency_rotation(rotation_manager):
    """Test emergency rotation procedure."""
    result = await rotation_manager.rotate_key(
        key_id="test_key",
        reason=RotationReason.SECURITY,
        rotated_by="security_team",
        emergency=True
    )
    
    assert result["success"] is True
    assert result["emergency"] is True
    
    # Verify shortened overlap period
    overlap_duration = (
        datetime.fromisoformat(result["overlap_ends_at"]) - 
        datetime.utcnow()
    )
    assert overlap_duration <= rotation_manager.config.emergency_overlap

@pytest.mark.asyncio
async def test_rotation_with_service_notification(rotation_manager, notifier):
    """Test rotation with service notifications."""
    await rotation_manager.rotate_key(
        key_id="test_key",
        reason=RotationReason.AGE,
        rotated_by="test_user"
    )
    
    # Verify notifications
    notifier.notify.assert_called_with(
        KeyEventType.ROTATED,
        key_id="test_key",
        service="test_service",
        metadata={
            "reason": RotationReason.AGE.value,
            "rotated_by": "test_user",
            "overlap_ends_at": mock.ANY
        }
    )

# Overlap Period Tests

@pytest.mark.asyncio
async def test_overlap_period_management(rotation_manager, key_manager):
    """Test overlap period handling."""
    # Rotate key
    result = await rotation_manager.rotate_key(
        key_id="test_key",
        reason=RotationReason.AGE,
        rotated_by="test_user"
    )
    
    # Verify old key not immediately revoked
    key_manager.revoke_key.assert_not_called()
    
    # Fast forward past overlap period
    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = datetime.fromisoformat(
            result["overlap_ends_at"]
        ) + timedelta(minutes=1)
        
        # Check rotation status again
        status = await rotation_manager.get_rotation_status("test_key")
        assert status["overlap_expired"] is True

@pytest.mark.asyncio
async def test_concurrent_rotation_prevention(rotation_manager):
    """Test prevention of concurrent rotations."""
    # Start first rotation
    rotation1 = rotation_manager.rotate_key(
        key_id="test_key",
        reason=RotationReason.AGE,
        rotated_by="user1"
    )
    
    # Attempt concurrent rotation
    with pytest.raises(Exception) as exc:
        await rotation_manager.rotate_key(
            key_id="test_key",
            reason=RotationReason.AGE,
            rotated_by="user2"
        )
    assert "Rotation already in progress" in str(exc.value)

# Error Handling Tests

@pytest.mark.asyncio
async def test_rotation_retry_mechanism(rotation_manager, key_manager):
    """Test rotation retry mechanism."""
    # Fail first attempt, succeed on retry
    key_manager.create_key.side_effect = [
        Exception("First attempt failed"),
        {
            "key_id": "new_key",
            "service": "test_service"
        }
    ]
    
    result = await rotation_manager.rotate_key(
        key_id="test_key",
        reason=RotationReason.AGE,
        rotated_by="test_user"
    )
    
    assert result["success"] is True
    assert key_manager.create_key.call_count == 2

@pytest.mark.asyncio
async def test_rotation_rollback(rotation_manager, key_manager):
    """Test rotation rollback on failure."""
    # Fail after new key creation
    key_manager.revoke_key.side_effect = Exception("Revocation failed")
    
    with pytest.raises(Exception):
        await rotation_manager.rotate_key(
            key_id="test_key",
            reason=RotationReason.AGE,
            rotated_by="test_user"
        )
    
    # Verify new key revoked during rollback
    key_manager.revoke_key.assert_called_with(
        mock.ANY,  # new key ID
        reason="rotation_rollback",
        revoked_by="system"
    )

# Audit Trail Tests

@pytest.mark.asyncio
async def test_rotation_audit_trail(rotation_manager, key_manager):
    """Test rotation audit trail maintenance."""
    await rotation_manager.rotate_key(
        key_id="test_key",
        reason=RotationReason.AGE,
        rotated_by="test_user"
    )
    
    # Verify audit events
    audit_calls = key_manager.audit.log_event.call_args_list
    assert any(
        call.args[0] == "key_rotation_started"
        for call in audit_calls
    )
    assert any(
        call.args[0] == "key_rotation_completed"
        for call in audit_calls
    ) 