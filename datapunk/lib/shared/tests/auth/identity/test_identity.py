"""
Identity Module Tests
----------------

Tests the identity management system including:
- Identity management
- Identity verification
- Profile management
- Federation services
- Type validation

Run with: pytest -v test_identity.py
"""

import pytest
from datetime import datetime, timedelta
import json
from unittest.mock import AsyncMock, Mock, patch

from datapunk_shared.auth.identity import (
    IdentityManager,
    IdentityVerifier,
    UserProfile,
    FederationService,
    IdentityType,
    ProviderType
)

# Test Fixtures

@pytest.fixture
def storage_client():
    """Mock storage client for testing."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.set = AsyncMock()
    client.delete = AsyncMock()
    return client

@pytest.fixture
def cache_client():
    """Mock cache client for testing."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.set = AsyncMock()
    client.delete = AsyncMock()
    return client

@pytest.fixture
def identity_manager(storage_client, cache_client):
    """Create identity manager for testing."""
    return IdentityManager(
        storage=storage_client,
        cache=cache_client
    )

@pytest.fixture
def identity_verifier():
    """Create identity verifier for testing."""
    return IdentityVerifier()

@pytest.fixture
def federation_service():
    """Create federation service for testing."""
    return FederationService()

# Identity Management Tests

@pytest.mark.asyncio
async def test_identity_creation(identity_manager):
    """Test identity creation."""
    # Create identity
    identity = await identity_manager.create_identity({
        "type": IdentityType.USER,
        "provider": ProviderType.LOCAL,
        "email": "test@example.com",
        "username": "testuser"
    })
    
    assert identity.id is not None
    assert identity.type == IdentityType.USER
    assert identity.provider == ProviderType.LOCAL
    assert identity.email == "test@example.com"
    
    # Verify storage
    identity_manager.storage.set.assert_called_once()

@pytest.mark.asyncio
async def test_identity_retrieval(identity_manager):
    """Test identity retrieval."""
    # Mock stored identity
    stored_identity = {
        "id": "test_id",
        "type": IdentityType.USER.value,
        "email": "test@example.com"
    }
    identity_manager.storage.get.return_value = stored_identity
    
    # Retrieve identity
    identity = await identity_manager.get_identity("test_id")
    assert identity.id == "test_id"
    assert identity.type == IdentityType.USER
    assert identity.email == "test@example.com"

# Identity Verification Tests

@pytest.mark.asyncio
async def test_verification_process(identity_verifier):
    """Test identity verification process."""
    # Start verification
    verification = await identity_verifier.start_verification(
        identity_id="test_id",
        method="email"
    )
    assert verification.id is not None
    assert verification.status == "pending"
    
    # Complete verification
    result = await identity_verifier.complete_verification(
        verification.id,
        code="123456"
    )
    assert result.success is True
    assert result.verified_at is not None

@pytest.mark.asyncio
async def test_verification_methods(identity_verifier):
    """Test different verification methods."""
    # Email verification
    email_result = await identity_verifier.verify_email(
        email="test@example.com",
        code="123456"
    )
    assert email_result.success is True
    
    # Phone verification
    phone_result = await identity_verifier.verify_phone(
        phone="+1234567890",
        code="123456"
    )
    assert phone_result.success is True

# Profile Management Tests

def test_profile_creation():
    """Test user profile creation."""
    profile = UserProfile(
        user_id="test_user",
        display_name="Test User",
        email="test@example.com",
        metadata={
            "location": "Test City",
            "language": "en"
        }
    )
    
    assert profile.user_id == "test_user"
    assert profile.display_name == "Test User"
    assert profile.email == "test@example.com"
    assert profile.metadata["location"] == "Test City"

def test_profile_validation():
    """Test profile validation."""
    # Valid profile
    valid_profile = UserProfile(
        user_id="test_user",
        email="test@example.com"
    )
    assert valid_profile.is_valid() is True
    
    # Invalid profile
    invalid_profile = UserProfile(
        user_id="test_user",
        email="invalid-email"
    )
    assert invalid_profile.is_valid() is False

# Federation Tests

@pytest.mark.asyncio
async def test_federation_provider(federation_service):
    """Test federation provider integration."""
    # Register provider
    provider = await federation_service.register_provider({
        "name": "test_provider",
        "type": ProviderType.OAUTH,
        "client_id": "test_client",
        "client_secret": "test_secret"
    })
    assert provider.name == "test_provider"
    assert provider.type == ProviderType.OAUTH
    
    # Verify provider
    assert await federation_service.verify_provider(provider.id) is True

@pytest.mark.asyncio
async def test_federation_authentication(federation_service):
    """Test federated authentication."""
    # Start auth flow
    auth_url = await federation_service.get_auth_url(
        provider="test_provider",
        redirect_uri="http://example.com/callback"
    )
    assert "oauth" in auth_url.lower()
    assert "redirect_uri" in auth_url
    
    # Complete auth flow
    result = await federation_service.complete_auth(
        provider="test_provider",
        code="test_code"
    )
    assert result.success is True
    assert result.identity is not None

# Type Tests

def test_identity_types():
    """Test identity type system."""
    # Type validation
    assert IdentityType.validate(IdentityType.USER) is True
    assert IdentityType.validate("invalid") is False
    
    # Type conversion
    assert IdentityType.from_string("user") == IdentityType.USER
    assert IdentityType.to_string(IdentityType.SERVICE) == "service"

def test_provider_types():
    """Test provider type system."""
    # Type validation
    assert ProviderType.validate(ProviderType.LOCAL) is True
    assert ProviderType.validate("invalid") is False
    
    # Type conversion
    assert ProviderType.from_string("oauth") == ProviderType.OAUTH
    assert ProviderType.to_string(ProviderType.SAML) == "saml"

# Performance Tests

@pytest.mark.asyncio
async def test_identity_performance(identity_manager):
    """Test identity management performance."""
    # Generate test identities
    identities = [
        {
            "type": IdentityType.USER,
            "email": f"test{i}@example.com",
            "username": f"user{i}"
        }
        for i in range(100)
    ]
    
    # Measure creation time
    start_time = datetime.utcnow()
    created = await asyncio.gather(*[
        identity_manager.create_identity(identity)
        for identity in identities
    ])
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 2.0  # Should create 100 identities within 2 seconds
    assert len(created) == 100

@pytest.mark.asyncio
async def test_verification_performance(identity_verifier):
    """Test verification performance."""
    # Generate verification requests
    requests = [
        (f"test{i}@example.com", "123456")
        for i in range(100)
    ]
    
    # Measure verification time
    start_time = datetime.utcnow()
    results = await asyncio.gather(*[
        identity_verifier.verify_email(email, code)
        for email, code in requests
    ])
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 1.0  # Should verify 100 emails within 1 second
    assert all(r.success for r in results) 