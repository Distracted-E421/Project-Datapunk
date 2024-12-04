"""
API Keys Test Suite
------------------

Tests the complete API key management system including:
- Key creation and validation
- Policy enforcement
- Key rotation
- Security controls
- Notifications
- Error handling

Run with: pytest -v test_api_keys.py
"""

import pytest
from datetime import datetime, timedelta, time
from unittest.mock import AsyncMock, Mock, patch
import secrets
import hashlib

from datapunk_shared.auth.api_keys import (
    APIKeyManager, KeyType, KeyPolicy, ComplianceRequirements,
    SecurityControls, ResourceQuota, TimeWindow, CircuitBreaker,
    KeyRotationManager, RotationReason, RotationConfig,
    KeyValidator, KeyValidationConfig, KeyNotifier, KeyEventType
)
from datapunk_shared.auth.api_keys.types import (
    KeyID, KeyHash, KeySecret, KeyValidationResult
)

# Test Fixtures

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.gauge = AsyncMock()
    return client

@pytest.fixture
def cache_client():
    """Mock cache client for testing."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    client.delete = AsyncMock()
    client.scan = AsyncMock(return_value=[])
    return client

@pytest.fixture
def audit_logger():
    """Mock audit logger for testing."""
    logger = AsyncMock()
    logger.log_event = AsyncMock()
    return logger

@pytest.fixture
def key_validator():
    """Create key validator with test configuration."""
    config = KeyValidationConfig(
        min_key_length=32,
        max_key_length=64,
        allowed_key_types={KeyType.SERVICE, KeyType.READ_ONLY}
    )
    return KeyValidator(config=config)

@pytest.fixture
def api_key_manager(cache_client, metrics_client, audit_logger, key_validator):
    """Create API key manager instance for testing."""
    return APIKeyManager(
        cache_client=cache_client,
        metrics=metrics_client,
        audit_logger=audit_logger,
        validator=key_validator
    )

@pytest.fixture
def rotation_manager(api_key_manager, metrics_client):
    """Create key rotation manager for testing."""
    config = RotationConfig(
        max_key_age=timedelta(days=90),
        overlap_period=timedelta(hours=24)
    )
    return KeyRotationManager(
        key_manager=api_key_manager,
        metrics=metrics_client,
        config=config
    )

# Key Management Tests

@pytest.mark.asyncio
async def test_create_key_success(api_key_manager):
    """Test successful API key creation."""
    service = "test_service"
    policy = KeyPolicy(
        type=KeyType.SERVICE,
        rate_limit=1000,
        allowed_paths={"/api/v1/*"},
        allowed_methods={"GET", "POST"}
    )
    
    result = await api_key_manager.create_key(
        service=service,
        policy=policy,
        created_by="test_user"
    )
    
    assert result["service"] == service
    assert "key" in result
    assert "key_id" in result
    assert "created_at" in result
    
    # Verify metrics and audit
    api_key_manager.metrics.increment.assert_called_with(
        "api_keys_created",
        {"service": service, "type": policy.type.value}
    )
    api_key_manager.audit.log_event.assert_called_once()

@pytest.mark.asyncio
async def test_create_key_with_ttl(api_key_manager):
    """Test key creation with expiration time."""
    ttl = timedelta(days=30)
    api_key_manager.key_ttl = ttl
    
    result = await api_key_manager.create_key(
        service="test_service",
        policy=KeyPolicy(type=KeyType.SERVICE),
        created_by="test_user"
    )
    
    assert "expires_at" in result
    expiry = datetime.fromisoformat(result["expires_at"])
    creation = datetime.fromisoformat(result["created_at"])
    assert (expiry - creation).days == 30

@pytest.mark.asyncio
async def test_create_key_validation_failure(api_key_manager):
    """Test key creation with invalid policy."""
    with pytest.raises(AuthError) as exc:
        await api_key_manager.create_key(
            service="test_service",
            policy=KeyPolicy(type=KeyType.ADMIN),  # Not in allowed types
            created_by="test_user"
        )
    assert "Invalid key configuration" in str(exc.value)

# Key Validation Tests

@pytest.mark.asyncio
async def test_key_validation_success(key_validator):
    """Test successful key validation."""
    key = secrets.token_urlsafe(32)
    policy = KeyPolicy(type=KeyType.SERVICE)
    
    result = await key_validator.validate_key(key, policy)
    
    assert result["valid"] is True
    assert not result["issues"]
    assert not result["warnings"]

@pytest.mark.asyncio
async def test_key_validation_format_failure(key_validator):
    """Test validation failure for invalid key format."""
    result = await key_validator.validate_key(
        "short_key",
        KeyPolicy(type=KeyType.SERVICE)
    )
    
    assert result["valid"] is False
    assert "Key too short" in result["issues"][0]

@pytest.mark.asyncio
async def test_key_validation_policy_restrictions(key_validator):
    """Test validation with policy restrictions."""
    key = secrets.token_urlsafe(32)
    policy = KeyPolicy(
        type=KeyType.ADMIN,  # Not in allowed types
        rate_limit=1000
    )
    
    result = await key_validator.validate_key(key, policy)
    
    assert result["valid"] is False
    assert any("not allowed" in issue for issue in result["issues"])

# Key Rotation Tests

@pytest.mark.asyncio
async def test_check_rotation_needed(rotation_manager, cache_client):
    """Test rotation check logic."""
    # Setup mock key data
    old_key_data = {
        "created_at": (datetime.utcnow() - timedelta(days=100)).isoformat(),
        "service": "test_service"
    }
    cache_client.get.return_value = old_key_data
    
    result = await rotation_manager.check_rotation_needed("test_key")
    
    assert result["needs_rotation"] is True
    assert "age" in result["reasons"]

@pytest.mark.asyncio
async def test_rotate_key_success(rotation_manager, cache_client):
    """Test successful key rotation."""
    # Setup mock existing key
    old_key_data = {
        "service": "test_service",
        "policy": {
            "type": KeyType.SERVICE.value,
            "rate_limit": 1000
        },
        "created_at": datetime.utcnow().isoformat()
    }
    cache_client.get.return_value = old_key_data
    
    result = await rotation_manager.rotate_key(
        key_id="test_key",
        reason=RotationReason.AGE,
        rotated_by="test_user"
    )
    
    assert result["success"] is True
    assert "new_key" in result
    assert "overlap_ends_at" in result

@pytest.mark.asyncio
async def test_emergency_rotation(rotation_manager):
    """Test emergency key rotation with shortened overlap."""
    result = await rotation_manager.rotate_key(
        key_id="test_key",
        reason=RotationReason.SECURITY,
        rotated_by="test_user",
        emergency=True
    )
    
    assert result["success"] is True
    assert result["emergency"] is True

# Policy Tests

def test_analytics_policy_template():
    """Test the pre-defined analytics policy template."""
    policy = ANALYTICS_POLICY
    
    assert policy.type == KeyType.ANALYTICS
    assert "/api/v1/analytics/" in policy.allowed_paths
    assert "GET" in policy.allowed_methods
    assert policy.compliance.audit_level == "detailed"

def test_emergency_policy_template():
    """Test the pre-defined emergency policy template."""
    policy = EMERGENCY_POLICY
    
    assert policy.type == KeyType.EMERGENCY
    assert policy.compliance.require_mfa is True
    assert policy.security.require_https is True
    assert policy.circuit_breaker.failure_threshold == 3

def test_temporary_policy_template():
    """Test the pre-defined temporary policy template."""
    policy = TEMPORARY_POLICY
    
    assert policy.type == KeyType.TEMPORARY
    assert len(policy.time_windows) == 1
    window = policy.time_windows[0]
    assert window.start_time == time(9, 0)
    assert window.end_time == time(17, 0)
    assert set(window.days) == {0, 1, 2, 3, 4}  # Monday-Friday

# Error Handling Tests

@pytest.mark.asyncio
async def test_create_key_cache_failure(api_key_manager, cache_client):
    """Test graceful handling of cache failures during key creation."""
    cache_client.set.side_effect = Exception("Cache connection failed")
    
    with pytest.raises(AuthError) as exc:
        await api_key_manager.create_key(
            service="test_service",
            policy=KeyPolicy(type=KeyType.SERVICE),
            created_by="test_user"
        )
    assert "Failed to create API key" in str(exc.value)

@pytest.mark.asyncio
async def test_rotate_key_not_found(rotation_manager, cache_client):
    """Test rotation of non-existent key."""
    cache_client.get.return_value = None
    
    with pytest.raises(AuthError) as exc:
        await rotation_manager.rotate_key(
            key_id="nonexistent_key",
            reason=RotationReason.AGE,
            rotated_by="test_user"
        )
    assert "Key not found" in str(exc.value)

@pytest.mark.asyncio
async def test_metrics_failure_handling(api_key_manager):
    """Test continued operation when metrics fail."""
    api_key_manager.metrics.increment.side_effect = Exception("Metrics failed")
    
    # Should still create key despite metrics failure
    result = await api_key_manager.create_key(
        service="test_service",
        policy=KeyPolicy(type=KeyType.SERVICE),
        created_by="test_user"
    )
    
    assert "key_id" in result 