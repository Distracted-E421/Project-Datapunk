"""
API Key Manager Tests
------------------

Tests the API key manager functionality including:
- Key lifecycle management (creation, validation, revocation)
- Policy enforcement and updates
- Cache integration
- Metrics collection
- Audit logging
- Security controls
- Error handling

Run with: pytest -v test_manager.py
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import hashlib
import secrets

from datapunk_shared.auth.api_keys import (
    APIKeyManager, KeyPolicy, KeyType,
    ComplianceRequirements, SecurityControls,
    KeyValidator, KeyValidationConfig
)
from datapunk_shared.auth.api_keys.types import KeyID, KeyHash, KeySecret

# Test Fixtures

@pytest.fixture
def cache_client():
    """Mock cache client for testing."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    client.delete = AsyncMock()
    return client

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.gauge = AsyncMock()
    client.timing = AsyncMock()
    return client

@pytest.fixture
def audit_logger():
    """Mock audit logger for testing."""
    logger = AsyncMock()
    logger.log_event = AsyncMock()
    return logger

@pytest.fixture
def validator():
    """Create key validator for testing."""
    config = KeyValidationConfig(
        min_key_length=32,
        max_key_length=64,
        allowed_key_types={KeyType.SERVICE, KeyType.READ_ONLY}
    )
    return KeyValidator(config=config)

@pytest.fixture
def key_manager(cache_client, metrics_client, audit_logger, validator):
    """Create API key manager instance for testing."""
    return APIKeyManager(
        cache_client=cache_client,
        metrics=metrics_client,
        audit_logger=audit_logger,
        validator=validator,
        key_ttl=timedelta(days=30)
    )

# Key Creation Tests

@pytest.mark.asyncio
async def test_create_key_success(key_manager):
    """Test successful key creation."""
    service = "test_service"
    policy = KeyPolicy(
        type=KeyType.SERVICE,
        rate_limit=1000,
        allowed_paths={"/api/v1/*"}
    )
    
    result = await key_manager.create_key(
        service=service,
        policy=policy,
        created_by="test_user"
    )
    
    # Verify key format
    assert "key_id" in result
    assert "key" in result
    assert result["service"] == service
    assert "created_at" in result
    assert "expires_at" in result
    
    # Verify storage
    key_manager.cache.set.assert_called_once()
    
    # Verify metrics
    key_manager.metrics.increment.assert_called_with(
        "api_keys_created",
        {"service": service, "type": policy.type.value}
    )
    
    # Verify audit
    key_manager.audit.log_event.assert_called_with(
        "api_key_created",
        {
            "key_id": result["key_id"],
            "service": service,
            "created_by": "test_user",
            "policy_type": policy.type.value
        }
    )

@pytest.mark.asyncio
async def test_create_key_with_metadata(key_manager):
    """Test key creation with metadata."""
    metadata = {
        "environment": "production",
        "team": "backend",
        "purpose": "service_auth"
    }
    
    result = await key_manager.create_key(
        service="test_service",
        policy=KeyPolicy(type=KeyType.SERVICE),
        created_by="test_user",
        metadata=metadata
    )
    
    # Verify metadata stored
    stored_data = key_manager.cache.set.call_args[0][1]
    assert stored_data["metadata"] == metadata

@pytest.mark.asyncio
async def test_create_key_validation_failure(key_manager):
    """Test key creation with invalid policy."""
    with pytest.raises(AuthError) as exc:
        await key_manager.create_key(
            service="test_service",
            policy=KeyPolicy(type=KeyType.ADMIN),  # Not allowed
            created_by="test_user"
        )
    assert "Invalid key configuration" in str(exc.value)

# Key Storage Tests

@pytest.mark.asyncio
async def test_key_storage_security(key_manager):
    """Test secure key storage practices."""
    result = await key_manager.create_key(
        service="test_service",
        policy=KeyPolicy(type=KeyType.SERVICE),
        created_by="test_user"
    )
    
    # Verify key hash stored (not plain text)
    stored_data = key_manager.cache.set.call_args[0][1]
    assert "key" not in stored_data
    assert "key_hash" in stored_data
    
    # Verify hash is correct
    key_hash = hashlib.sha256(result["key"].encode()).hexdigest()
    assert stored_data["key_hash"] == key_hash

@pytest.mark.asyncio
async def test_key_ttl_handling(key_manager):
    """Test key TTL configuration."""
    result = await key_manager.create_key(
        service="test_service",
        policy=KeyPolicy(type=KeyType.SERVICE),
        created_by="test_user"
    )
    
    # Verify TTL set in cache
    cache_ttl = key_manager.cache.set.call_args[1]["ttl"]
    assert cache_ttl == int(key_manager.key_ttl.total_seconds())
    
    # Verify expiry time in response
    expiry = datetime.fromisoformat(result["expires_at"])
    creation = datetime.fromisoformat(result["created_at"])
    assert (expiry - creation).days == 30

# Key Validation Tests

@pytest.mark.asyncio
async def test_validate_key_success(key_manager, cache_client):
    """Test successful key validation."""
    # Setup existing key
    key_data = {
        "key_hash": hashlib.sha256("test_key".encode()).hexdigest(),
        "service": "test_service",
        "policy": {
            "type": KeyType.SERVICE.value,
            "rate_limit": 1000
        }
    }
    cache_client.get.return_value = key_data
    
    result = await key_manager.validate_key(
        "test_key",
        required_scopes=["read"]
    )
    
    assert result is not None
    assert result["service"] == "test_service"
    
    # Verify last used updated
    stored_data = key_manager.cache.set.call_args[0][1]
    assert "last_used" in stored_data

@pytest.mark.asyncio
async def test_validate_key_failure(key_manager):
    """Test key validation failures."""
    # Non-existent key
    result = await key_manager.validate_key("nonexistent_key")
    assert result is None
    
    # Invalid hash
    key_data = {
        "key_hash": "different_hash",
        "service": "test_service"
    }
    key_manager.cache.get.return_value = key_data
    
    result = await key_manager.validate_key("test_key")
    assert result is None

@pytest.mark.asyncio
async def test_validate_key_scope_check(key_manager, cache_client):
    """Test key validation with scope checking."""
    # Setup key with scopes
    key_data = {
        "key_hash": hashlib.sha256("test_key".encode()).hexdigest(),
        "service": "test_service",
        "policy": {
            "type": KeyType.SERVICE.value,
            "scopes": ["read", "write"]
        }
    }
    cache_client.get.return_value = key_data
    
    # Valid scope
    result = await key_manager.validate_key(
        "test_key",
        required_scopes=["read"]
    )
    assert result is not None
    
    # Invalid scope
    result = await key_manager.validate_key(
        "test_key",
        required_scopes=["admin"]
    )
    assert result is None

# Key Revocation Tests

@pytest.mark.asyncio
async def test_revoke_key_success(key_manager, cache_client):
    """Test successful key revocation."""
    # Setup existing key
    key_data = {
        "service": "test_service",
        "policy": {"type": KeyType.SERVICE.value}
    }
    cache_client.get.return_value = key_data
    
    result = await key_manager.revoke_key(
        key_id="test_key",
        reason="security_incident",
        revoked_by="security_team"
    )
    
    assert result is True
    
    # Verify key updated
    stored_data = key_manager.cache.set.call_args[0][1]
    assert stored_data["status"] == "revoked"
    assert stored_data["revoked_at"]
    assert stored_data["revoked_by"] == "security_team"
    assert stored_data["revocation_reason"] == "security_incident"
    
    # Verify audit
    key_manager.audit.log_event.assert_called_with(
        "api_key_revoked",
        {
            "key_id": "test_key",
            "service": "test_service",
            "revoked_by": "security_team",
            "reason": "security_incident"
        }
    )

@pytest.mark.asyncio
async def test_revoke_key_not_found(key_manager):
    """Test revocation of non-existent key."""
    with pytest.raises(AuthError) as exc:
        await key_manager.revoke_key(
            key_id="nonexistent_key",
            reason="test",
            revoked_by="test_user"
        )
    assert "Key not found" in str(exc.value)

# Policy Update Tests

@pytest.mark.asyncio
async def test_update_policy_success(key_manager, cache_client):
    """Test successful policy update."""
    # Setup existing key
    old_policy = {
        "type": KeyType.SERVICE.value,
        "rate_limit": 1000
    }
    key_data = {
        "service": "test_service",
        "policy": old_policy
    }
    cache_client.get.return_value = key_data
    
    new_policy = KeyPolicy(
        type=KeyType.SERVICE,
        rate_limit=2000
    )
    
    result = await key_manager.update_policy(
        key_id="test_key",
        new_policy=new_policy,
        updated_by="test_user"
    )
    
    assert result["policy"]["rate_limit"] == 2000
    
    # Verify audit
    key_manager.audit.log_event.assert_called_with(
        "api_key_policy_updated",
        {
            "key_id": "test_key",
            "service": "test_service",
            "updated_by": "test_user",
            "old_policy": old_policy,
            "new_policy": vars(new_policy)
        }
    )

# Error Handling Tests

@pytest.mark.asyncio
async def test_cache_failure_handling(key_manager):
    """Test handling of cache failures."""
    key_manager.cache.set.side_effect = Exception("Cache error")
    
    with pytest.raises(AuthError) as exc:
        await key_manager.create_key(
            service="test_service",
            policy=KeyPolicy(type=KeyType.SERVICE),
            created_by="test_user"
        )
    assert "Failed to create API key" in str(exc.value)

@pytest.mark.asyncio
async def test_metrics_failure_handling(key_manager):
    """Test handling of metrics failures."""
    key_manager.metrics.increment.side_effect = Exception("Metrics error")
    
    # Should still create key despite metrics failure
    result = await key_manager.create_key(
        service="test_service",
        policy=KeyPolicy(type=KeyType.SERVICE),
        created_by="test_user"
    )
    
    assert "key_id" in result

# Performance Monitoring Tests

@pytest.mark.asyncio
async def test_performance_metrics(key_manager):
    """Test performance metric collection."""
    await key_manager.create_key(
        service="test_service",
        policy=KeyPolicy(type=KeyType.SERVICE),
        created_by="test_user"
    )
    
    # Verify timing metrics
    key_manager.metrics.timing.assert_called_with(
        "api_key_creation_time",
        mock.ANY,
        tags={"service": "test_service"}
    )

# Security Tests

@pytest.mark.asyncio
async def test_key_entropy(key_manager):
    """Test key generation entropy."""
    result = await key_manager.create_key(
        service="test_service",
        policy=KeyPolicy(type=KeyType.SERVICE),
        created_by="test_user"
    )
    
    key = result["key"]
    # Should be at least 32 bytes of entropy
    assert len(key) >= 43  # Base64 encoding of 32 bytes

@pytest.mark.asyncio
async def test_key_uniqueness(key_manager):
    """Test key uniqueness."""
    keys = set()
    for _ in range(100):
        result = await key_manager.create_key(
            service="test_service",
            policy=KeyPolicy(type=KeyType.SERVICE),
            created_by="test_user"
        )
        keys.add(result["key"])
    
    # All keys should be unique
    assert len(keys) == 100 