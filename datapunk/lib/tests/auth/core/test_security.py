"""
Core Security Tests
--------------

Tests the core security system including:
- Authentication
- Authorization
- Encryption
- Token management
- Security policies
- Threat detection
- Audit logging

Run with: pytest -v test_security.py
"""

import pytest
from datetime import datetime, timedelta
import json
from unittest.mock import AsyncMock, Mock, patch
import secrets
import hashlib

from datapunk_shared.auth.core.security import (
    SecurityManager,
    SecurityPolicy,
    Encryptor,
    TokenManager,
    SecurityContext,
    ThreatDetector,
    SecurityAuditor
)
from datapunk_shared.auth.core.exceptions import SecurityError

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
def security_policy():
    """Create security policy for testing."""
    return SecurityPolicy(
        password_min_length=12,
        password_complexity=True,
        mfa_required=False,
        session_timeout=timedelta(hours=1),
        max_login_attempts=3
    )

@pytest.fixture
def security_manager(storage_client, cache_client, security_policy):
    """Create security manager for testing."""
    return SecurityManager(
        storage=storage_client,
        cache=cache_client,
        policy=security_policy
    )

@pytest.fixture
def security_context():
    """Create security context for testing."""
    return SecurityContext(
        user_id="test_user",
        ip_address="127.0.0.1",
        user_agent="test_agent",
        timestamp=datetime.utcnow()
    )

# Authentication Tests

@pytest.mark.asyncio
async def test_password_authentication(security_manager):
    """Test password authentication."""
    # Hash password
    password = "SecurePass123!"
    salt = secrets.token_hex(16)
    hashed = security_manager.hash_password(password, salt)
    
    # Store credentials
    security_manager.storage.get.return_value = {
        "password_hash": hashed,
        "salt": salt
    }
    
    # Valid authentication
    result = await security_manager.authenticate_password(
        "test_user",
        password
    )
    assert result.success is True
    assert result.user_id == "test_user"
    
    # Invalid password
    result = await security_manager.authenticate_password(
        "test_user",
        "WrongPass123!"
    )
    assert result.success is False

@pytest.mark.asyncio
async def test_token_authentication(security_manager):
    """Test token authentication."""
    # Generate token
    token = security_manager.generate_token()
    
    # Store token
    security_manager.storage.get.return_value = {
        "token": token,
        "user_id": "test_user",
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }
    
    # Valid token
    result = await security_manager.authenticate_token(token)
    assert result.success is True
    assert result.user_id == "test_user"
    
    # Invalid token
    result = await security_manager.authenticate_token("invalid_token")
    assert result.success is False

# Authorization Tests

@pytest.mark.asyncio
async def test_permission_check(security_manager):
    """Test permission checking."""
    # Setup permissions
    security_manager.storage.get.return_value = {
        "roles": ["admin"],
        "permissions": ["read", "write"]
    }
    
    # Check permission
    result = await security_manager.check_permission(
        user_id="test_user",
        permission="write",
        resource="document"
    )
    assert result.allowed is True
    
    # Check denied permission
    result = await security_manager.check_permission(
        user_id="test_user",
        permission="delete",
        resource="document"
    )
    assert result.allowed is False

@pytest.mark.asyncio
async def test_role_based_access(security_manager):
    """Test role-based access control."""
    # Setup roles
    security_manager.storage.get.return_value = {
        "roles": ["editor"],
        "role_permissions": {
            "editor": ["read", "write", "update"]
        }
    }
    
    # Check allowed action
    result = await security_manager.check_role_access(
        user_id="test_user",
        action="write",
        resource="document"
    )
    assert result.allowed is True
    
    # Check denied action
    result = await security_manager.check_role_access(
        user_id="test_user",
        action="delete",
        resource="document"
    )
    assert result.allowed is False

# Encryption Tests

def test_data_encryption(security_manager):
    """Test data encryption."""
    # Test data
    sensitive_data = "sensitive information"
    
    # Encrypt data
    encrypted = security_manager.encrypt_data(sensitive_data)
    assert encrypted != sensitive_data
    
    # Decrypt data
    decrypted = security_manager.decrypt_data(encrypted)
    assert decrypted == sensitive_data

def test_key_rotation(security_manager):
    """Test encryption key rotation."""
    # Generate new key
    new_key = security_manager.generate_encryption_key()
    
    # Rotate key
    security_manager.rotate_encryption_key(new_key)
    
    # Verify key rotation
    assert security_manager.current_key == new_key
    assert new_key in security_manager.key_history

# Token Management Tests

def test_token_generation(security_manager):
    """Test token generation."""
    token = security_manager.generate_token()
    assert len(token) >= 32
    assert isinstance(token, str)
    
    # Generate multiple tokens
    tokens = [security_manager.generate_token() for _ in range(10)]
    assert len(set(tokens)) == 10  # All unique

def test_token_validation(security_manager):
    """Test token validation."""
    # Generate token
    token = security_manager.generate_token()
    
    # Valid token
    assert security_manager.validate_token_format(token) is True
    
    # Invalid token
    assert security_manager.validate_token_format("invalid") is False
    assert security_manager.validate_token_format("") is False

# Security Policy Tests

def test_password_policy(security_manager):
    """Test password policy enforcement."""
    policy = security_manager.policy
    
    # Valid password
    assert policy.validate_password("SecurePass123!") is True
    
    # Invalid passwords
    assert policy.validate_password("short") is False  # Too short
    assert policy.validate_password("nodigits") is False  # No digits
    assert policy.validate_password("no-upper-case-123") is False  # No uppercase

def test_session_policy(security_manager):
    """Test session policy enforcement."""
    policy = security_manager.policy
    
    # Valid session
    session = {
        "created_at": datetime.utcnow(),
        "last_activity": datetime.utcnow()
    }
    assert policy.validate_session(session) is True
    
    # Expired session
    expired_session = {
        "created_at": datetime.utcnow() - timedelta(days=1),
        "last_activity": datetime.utcnow() - timedelta(hours=2)
    }
    assert policy.validate_session(expired_session) is False

# Threat Detection Tests

@pytest.mark.asyncio
async def test_threat_detection(security_manager):
    """Test threat detection."""
    detector = ThreatDetector()
    
    # Normal activity
    context = SecurityContext(
        user_id="test_user",
        ip_address="127.0.0.1",
        action="login"
    )
    result = await detector.analyze(context)
    assert result.threat_level == "low"
    
    # Suspicious activity
    suspicious_context = SecurityContext(
        user_id="test_user",
        ip_address="1.2.3.4",
        action="login",
        failed_attempts=5
    )
    result = await detector.analyze(suspicious_context)
    assert result.threat_level == "high"

@pytest.mark.asyncio
async def test_brute_force_detection(security_manager):
    """Test brute force attack detection."""
    # Simulate login attempts
    for _ in range(3):
        await security_manager.record_failed_login("test_user")
    
    # Check if account is locked
    status = await security_manager.get_account_status("test_user")
    assert status.locked is True
    assert status.unlock_time > datetime.utcnow()

# Audit Logging Tests

@pytest.mark.asyncio
async def test_security_audit(security_manager):
    """Test security audit logging."""
    auditor = SecurityAuditor()
    
    # Log security event
    event = {
        "type": "authentication",
        "user_id": "test_user",
        "action": "login",
        "success": True,
        "timestamp": datetime.utcnow()
    }
    await auditor.log_event(event)
    
    # Verify audit log
    logs = await auditor.get_logs(user_id="test_user")
    assert len(logs) > 0
    assert logs[0]["type"] == "authentication"
    assert logs[0]["action"] == "login"

@pytest.mark.asyncio
async def test_audit_reporting(security_manager):
    """Test audit report generation."""
    auditor = SecurityAuditor()
    
    # Generate report
    report = await auditor.generate_report(
        start_time=datetime.utcnow() - timedelta(days=1),
        end_time=datetime.utcnow()
    )
    
    assert "security_events" in report
    assert "threat_summary" in report
    assert "recommendations" in report

# Performance Tests

@pytest.mark.asyncio
async def test_authentication_performance(security_manager):
    """Test authentication performance."""
    # Setup test data
    password = "SecurePass123!"
    salt = secrets.token_hex(16)
    hashed = security_manager.hash_password(password, salt)
    
    security_manager.storage.get.return_value = {
        "password_hash": hashed,
        "salt": salt
    }
    
    # Measure authentication time
    start_time = datetime.utcnow()
    for _ in range(100):
        await security_manager.authenticate_password(
            "test_user",
            password
        )
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 1.0  # Should authenticate 100 requests within 1 second

@pytest.mark.asyncio
async def test_encryption_performance(security_manager):
    """Test encryption performance."""
    # Generate test data
    data = "sensitive information" * 100  # 1.9KB
    
    # Measure encryption time
    start_time = datetime.utcnow()
    for _ in range(1000):
        encrypted = security_manager.encrypt_data(data)
        decrypted = security_manager.decrypt_data(encrypted)
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 2.0  # Should process 1000 encryption/decryption cycles within 2 seconds 