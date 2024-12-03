"""
Core Session Tests
-------------

Tests the core session management system including:
- Session creation
- Session validation
- Session storage
- Session expiration
- Token management
- Security controls
- Performance monitoring

Run with: pytest -v test_session.py
"""

import pytest
from datetime import datetime, timedelta
import json
from unittest.mock import AsyncMock, Mock, patch

from datapunk_shared.auth.core.session import (
    SessionManager,
    Session,
    SessionToken,
    SessionConfig,
    SessionContext,
    SessionStore,
    TokenGenerator
)
from datapunk_shared.auth.core.exceptions import SessionError

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
def session_config():
    """Create session configuration for testing."""
    return SessionConfig(
        ttl=timedelta(hours=1),
        max_sessions=5,
        refresh_ttl=timedelta(days=7),
        require_mfa=False
    )

@pytest.fixture
def session_manager(storage_client, cache_client, session_config):
    """Create session manager for testing."""
    return SessionManager(
        storage=storage_client,
        cache=cache_client,
        config=session_config
    )

@pytest.fixture
def session_context():
    """Create session context for testing."""
    return SessionContext(
        user_id="test_user",
        device_id="test_device",
        ip_address="127.0.0.1",
        user_agent="test_agent"
    )

# Session Creation Tests

@pytest.mark.asyncio
async def test_session_creation(session_manager, session_context):
    """Test session creation."""
    session = await session_manager.create_session(session_context)
    
    assert session.id is not None
    assert session.user_id == "test_user"
    assert session.token is not None
    assert session.expires_at > datetime.utcnow()
    
    # Verify storage
    session_manager.storage.set.assert_called_once()
    session_manager.cache.set.assert_called_once()

def test_session_validation():
    """Test session validation."""
    # Valid session
    session = Session(
        id="test_session",
        user_id="test_user",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    assert session.is_valid() is True
    
    # Expired session
    expired_session = Session(
        id="expired",
        user_id="test_user",
        created_at=datetime.utcnow() - timedelta(hours=2),
        expires_at=datetime.utcnow() - timedelta(hours=1)
    )
    assert expired_session.is_valid() is False

# Token Management Tests

def test_token_generation():
    """Test session token generation."""
    generator = TokenGenerator()
    
    token = generator.generate_token()
    assert len(token) >= 32
    assert isinstance(token, str)
    
    # Generate multiple tokens
    tokens = [generator.generate_token() for _ in range(10)]
    assert len(set(tokens)) == 10  # All unique

def test_token_validation():
    """Test token validation."""
    token = SessionToken(
        value="test_token",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    
    # Valid token
    assert token.is_valid() is True
    
    # Expired token
    expired_token = SessionToken(
        value="expired_token",
        expires_at=datetime.utcnow() - timedelta(hours=1)
    )
    assert expired_token.is_valid() is False

# Session Storage Tests

@pytest.mark.asyncio
async def test_session_storage(session_manager, session_context):
    """Test session storage operations."""
    # Create and store session
    session = await session_manager.create_session(session_context)
    
    # Mock storage response
    session_manager.storage.get.return_value = session.to_dict()
    
    # Retrieve session
    retrieved = await session_manager.get_session(session.id)
    assert retrieved.id == session.id
    assert retrieved.user_id == session.user_id
    
    # Delete session
    await session_manager.delete_session(session.id)
    session_manager.storage.delete.assert_called_once_with(session.id)
    session_manager.cache.delete.assert_called_once_with(session.id)

@pytest.mark.asyncio
async def test_session_caching(session_manager, session_context):
    """Test session caching."""
    session = await session_manager.create_session(session_context)
    
    # First retrieval (from storage)
    session_manager.cache.get.return_value = None
    await session_manager.get_session(session.id)
    assert session_manager.storage.get.called
    
    # Second retrieval (from cache)
    session_manager.cache.get.return_value = session.to_dict()
    await session_manager.get_session(session.id)
    assert session_manager.storage.get.call_count == 1  # Not called again

# Session Expiration Tests

@pytest.mark.asyncio
async def test_session_expiration(session_manager, session_context):
    """Test session expiration handling."""
    # Create session with short TTL
    session_manager.config.ttl = timedelta(seconds=1)
    session = await session_manager.create_session(session_context)
    
    # Wait for expiration
    await asyncio.sleep(1.1)
    
    # Try to get expired session
    with pytest.raises(SessionError) as exc:
        await session_manager.get_session(session.id)
    assert "expired" in str(exc.value).lower()

@pytest.mark.asyncio
async def test_session_refresh(session_manager, session_context):
    """Test session refresh."""
    session = await session_manager.create_session(session_context)
    original_expiry = session.expires_at
    
    # Refresh session
    refreshed = await session_manager.refresh_session(session.id)
    assert refreshed.expires_at > original_expiry
    
    # Verify storage updated
    session_manager.storage.set.assert_called_with(
        session.id,
        refreshed.to_dict()
    )

# Security Tests

@pytest.mark.asyncio
async def test_session_security(session_manager):
    """Test session security controls."""
    # Enable security mode
    session_manager.enable_security()
    
    # Test with suspicious context
    context = SessionContext(
        user_id="test_user",
        ip_address="1.2.3.4",
        risk_score=0.9  # High risk
    )
    
    with pytest.raises(SecurityError) as exc:
        await session_manager.create_session(context)
    assert "security risk" in str(exc.value).lower()

@pytest.mark.asyncio
async def test_mfa_requirement(session_manager, session_context):
    """Test MFA requirement."""
    # Enable MFA
    session_manager.config.require_mfa = True
    
    # Try to create session without MFA
    with pytest.raises(SecurityError) as exc:
        await session_manager.create_session(session_context)
    assert "mfa required" in str(exc.value).lower()
    
    # Create session with MFA
    session_context.mfa_verified = True
    session = await session_manager.create_session(session_context)
    assert session.mfa_verified is True

# Performance Tests

@pytest.mark.asyncio
async def test_session_performance(session_manager):
    """Test session management performance."""
    contexts = [
        SessionContext(user_id=f"user_{i}")
        for i in range(100)
    ]
    
    # Test creation performance
    start_time = datetime.utcnow()
    sessions = await asyncio.gather(*[
        session_manager.create_session(ctx)
        for ctx in contexts
    ])
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 2.0  # Should create 100 sessions within 2 seconds
    assert len(sessions) == 100

@pytest.mark.asyncio
async def test_concurrent_sessions(session_manager, session_context):
    """Test concurrent session handling."""
    # Create maximum allowed sessions
    max_sessions = session_manager.config.max_sessions
    for _ in range(max_sessions):
        await session_manager.create_session(session_context)
    
    # Try to create one more
    with pytest.raises(SessionError) as exc:
        await session_manager.create_session(session_context)
    assert "maximum sessions" in str(exc.value).lower()

# Cleanup Tests

@pytest.mark.asyncio
async def test_session_cleanup(session_manager):
    """Test session cleanup."""
    # Mock expired sessions
    session_manager.storage.list.return_value = [
        {
            "id": f"session_{i}",
            "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
        }
        for i in range(10)
    ]
    
    # Run cleanup
    result = await session_manager.cleanup_expired_sessions()
    
    assert result.cleaned == 10
    assert session_manager.storage.delete.call_count == 10
    assert session_manager.cache.delete.call_count == 10

@pytest.mark.asyncio
async def test_bulk_operations(session_manager):
    """Test bulk session operations."""
    # Create bulk sessions
    sessions = [
        Session(
            id=f"session_{i}",
            user_id="test_user",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        for i in range(100)
    ]
    
    # Test bulk storage
    start_time = datetime.utcnow()
    await session_manager.store_sessions(sessions)
    end_time = datetime.utcnow()
    
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 1.0  # Should store 100 sessions within 1 second
    
    # Verify batch optimization
    assert session_manager.storage.set.call_count < 10  # Should use batching 