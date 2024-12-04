"""
API Key Validation Tests
---------------------

Tests the validation system for API keys including:
- Key format validation
- Policy compliance checks
- Schema validation
- Custom validation rules
- Validation caching
- Performance monitoring

Run with: pytest -v test_validation.py
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from datapunk_shared.auth.api_keys import (
    KeyValidator, KeyValidationConfig, KeyPolicy,
    KeyType, ComplianceRequirements, SecurityControls
)
from datapunk_shared.auth.api_keys.types import KeyValidationResult

# Test Fixtures

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.timing = AsyncMock()
    return client

@pytest.fixture
def cache_client():
    """Mock cache client for testing."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    return client

@pytest.fixture
def validation_config():
    """Create validation configuration for testing."""
    return KeyValidationConfig(
        min_key_length=32,
        max_key_length=64,
        allowed_key_types={KeyType.SERVICE, KeyType.READ_ONLY},
        allowed_algorithms={"HS256", "HS512"},
        cache_ttl=timedelta(minutes=5)
    )

@pytest.fixture
def key_validator(metrics_client, cache_client, validation_config):
    """Create key validator instance for testing."""
    return KeyValidator(
        metrics=metrics_client,
        cache=cache_client,
        config=validation_config
    )

# Format Validation Tests

@pytest.mark.asyncio
async def test_key_format_validation(key_validator):
    """Test key format validation rules."""
    # Valid key
    valid_key = "x" * 32  # 32 characters
    result = await key_validator.validate_key_format(valid_key)
    assert result["valid"] is True
    
    # Too short
    short_key = "x" * 16
    result = await key_validator.validate_key_format(short_key)
    assert result["valid"] is False
    assert "too short" in result["issues"][0].lower()
    
    # Too long
    long_key = "x" * 128
    result = await key_validator.validate_key_format(long_key)
    assert result["valid"] is False
    assert "too long" in result["issues"][0].lower()

@pytest.mark.asyncio
async def test_key_character_validation(key_validator):
    """Test key character set validation."""
    # Valid characters
    valid_key = "abcdef0123456789ABCDEF" + "x" * 10
    result = await key_validator.validate_key_format(valid_key)
    assert result["valid"] is True
    
    # Invalid characters
    invalid_key = "test!@#$%^&*()" + "x" * 22
    result = await key_validator.validate_key_format(invalid_key)
    assert result["valid"] is False
    assert "invalid characters" in result["issues"][0].lower()

# Policy Validation Tests

@pytest.mark.asyncio
async def test_policy_type_validation(key_validator):
    """Test key type validation against policy."""
    # Allowed type
    policy = KeyPolicy(type=KeyType.SERVICE)
    result = await key_validator.validate_policy(policy)
    assert result["valid"] is True
    
    # Disallowed type
    policy = KeyPolicy(type=KeyType.ADMIN)
    result = await key_validator.validate_policy(policy)
    assert result["valid"] is False
    assert "key type not allowed" in result["issues"][0].lower()

@pytest.mark.asyncio
async def test_security_requirements_validation(key_validator):
    """Test security requirements validation."""
    policy = KeyPolicy(
        type=KeyType.SERVICE,
        security=SecurityControls(
            require_https=True,
            min_tls_version="1.1"  # Too low
        )
    )
    
    result = await key_validator.validate_policy(policy)
    assert result["valid"] is False
    assert any("tls version" in issue.lower() for issue in result["issues"])

# Schema Validation Tests

@pytest.mark.asyncio
async def test_key_schema_validation(key_validator):
    """Test key schema validation."""
    # Valid schema
    valid_key = {
        "id": "test_key",
        "type": KeyType.SERVICE.value,
        "created_at": datetime.utcnow().isoformat()
    }
    result = await key_validator.validate_schema(valid_key)
    assert result["valid"] is True
    
    # Missing required field
    invalid_key = {
        "id": "test_key",
        "type": KeyType.SERVICE.value
    }
    result = await key_validator.validate_schema(invalid_key)
    assert result["valid"] is False
    assert "missing field" in result["issues"][0].lower()

@pytest.mark.asyncio
async def test_policy_schema_validation(key_validator):
    """Test policy schema validation."""
    # Valid schema
    valid_policy = {
        "type": KeyType.SERVICE.value,
        "rate_limit": 1000,
        "allowed_paths": ["/api/v1/*"]
    }
    result = await key_validator.validate_schema(valid_policy, schema_type="policy")
    assert result["valid"] is True
    
    # Invalid rate limit
    invalid_policy = {
        "type": KeyType.SERVICE.value,
        "rate_limit": -1  # Negative rate limit
    }
    result = await key_validator.validate_schema(invalid_policy, schema_type="policy")
    assert result["valid"] is False
    assert "rate limit" in result["issues"][0].lower()

# Custom Validation Rules

@pytest.mark.asyncio
async def test_custom_validation_rules(key_validator):
    """Test custom validation rule enforcement."""
    # Add custom rule
    async def validate_prefix(key: str) -> bool:
        return key.startswith("test_")
    
    key_validator.add_custom_rule("prefix_check", validate_prefix)
    
    # Test custom rule
    result = await key_validator.validate_key(
        "test_valid_key" + "x" * 20,
        KeyPolicy(type=KeyType.SERVICE)
    )
    assert result["valid"] is True
    
    result = await key_validator.validate_key(
        "invalid_key" + "x" * 20,
        KeyPolicy(type=KeyType.SERVICE)
    )
    assert result["valid"] is False
    assert "prefix" in result["issues"][0].lower()

@pytest.mark.asyncio
async def test_validation_rule_priority(key_validator):
    """Test validation rule priority ordering."""
    # Format check should run before custom rules
    key_validator.add_custom_rule(
        "never_runs",
        lambda k: True
    )
    
    result = await key_validator.validate_key(
        "short",  # Too short, should fail before custom rule
        KeyPolicy(type=KeyType.SERVICE)
    )
    assert result["valid"] is False
    assert "length" in result["issues"][0].lower()

# Validation Caching Tests

@pytest.mark.asyncio
async def test_validation_result_caching(key_validator, cache_client):
    """Test caching of validation results."""
    key = "test_key" + "x" * 24
    policy = KeyPolicy(type=KeyType.SERVICE)
    
    # First validation - should check and cache
    result1 = await key_validator.validate_key(key, policy)
    assert result1["valid"] is True
    cache_client.set.assert_called_once()
    
    # Second validation - should use cache
    cache_client.get.return_value = {"valid": True, "cached": True}
    result2 = await key_validator.validate_key(key, policy)
    assert result2["valid"] is True
    assert result2.get("cached") is True

@pytest.mark.asyncio
async def test_cache_invalidation(key_validator, cache_client):
    """Test cache invalidation on policy changes."""
    key = "test_key" + "x" * 24
    policy = KeyPolicy(type=KeyType.SERVICE)
    
    # Cache initial validation
    await key_validator.validate_key(key, policy)
    
    # Policy change should invalidate cache
    policy.rate_limit = 2000
    cache_client.delete.assert_called_once()
    
    # Should revalidate
    result = await key_validator.validate_key(key, policy)
    assert not result.get("cached")

# Performance Monitoring Tests

@pytest.mark.asyncio
async def test_validation_performance_metrics(key_validator, metrics_client):
    """Test performance metric collection."""
    key = "test_key" + "x" * 24
    policy = KeyPolicy(type=KeyType.SERVICE)
    
    await key_validator.validate_key(key, policy)
    
    # Should record validation time
    metrics_client.timing.assert_called_with(
        "key_validation_time",
        mock.ANY,
        tags={"type": KeyType.SERVICE.value}
    )
    
    # Should increment validation counter
    metrics_client.increment.assert_called_with(
        "key_validations",
        tags={"type": KeyType.SERVICE.value, "result": "success"}
    )

@pytest.mark.asyncio
async def test_validation_error_metrics(key_validator, metrics_client):
    """Test error metric collection."""
    # Trigger validation error
    await key_validator.validate_key(
        "short",  # Invalid key
        KeyPolicy(type=KeyType.SERVICE)
    )
    
    # Should record validation failure
    metrics_client.increment.assert_called_with(
        "key_validations",
        tags={"type": KeyType.SERVICE.value, "result": "failure"}
    )

# Error Handling Tests

@pytest.mark.asyncio
async def test_validation_error_handling(key_validator):
    """Test graceful error handling."""
    # Invalid policy type
    result = await key_validator.validate_key(
        "test_key" + "x" * 24,
        None  # Invalid policy
    )
    assert result["valid"] is False
    assert "invalid policy" in result["issues"][0].lower()
    
    # Schema validation error
    result = await key_validator.validate_schema(
        {"invalid": "schema"},
        schema_type="unknown"  # Invalid schema type
    )
    assert result["valid"] is False
    assert "schema" in result["issues"][0].lower()

@pytest.mark.asyncio
async def test_cache_error_handling(key_validator, cache_client):
    """Test handling of cache failures."""
    cache_client.get.side_effect = Exception("Cache error")
    
    # Should continue validation despite cache error
    result = await key_validator.validate_key(
        "test_key" + "x" * 24,
        KeyPolicy(type=KeyType.SERVICE)
    )
    assert result["valid"] is True  # Should still validate
    assert not result.get("cached")  # Should not use cache 