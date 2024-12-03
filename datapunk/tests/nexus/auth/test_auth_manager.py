import pytest
from datetime import timedelta
from src.nexus.auth.auth_manager import AuthManager, AuthConfig, AuthProvider
import jwt
import time

@pytest.fixture
def auth_config():
    return AuthConfig(
        secret_key="test_secret_key",
        token_expiry=timedelta(minutes=15),
        refresh_token_expiry=timedelta(days=7),
        allowed_providers=[AuthProvider.INTERNAL]
    )

@pytest.fixture
def auth_manager(auth_config):
    return AuthManager(auth_config)

def test_generate_jwt(auth_manager):
    user_id = "test_user"
    claims = {"role": "admin"}
    
    access_token, refresh_token = auth_manager.generate_jwt(user_id, claims)
    
    # Verify access token
    access_payload = jwt.decode(access_token, auth_manager.config.secret_key, algorithms=["HS256"])
    assert access_payload["sub"] == user_id
    assert access_payload["role"] == "admin"
    assert access_payload["type"] == "access"
    
    # Verify refresh token
    refresh_payload = jwt.decode(refresh_token, auth_manager.config.secret_key, algorithms=["HS256"])
    assert refresh_payload["sub"] == user_id
    assert refresh_payload["type"] == "refresh"
    assert "jti" in refresh_payload

def test_validate_token(auth_manager):
    user_id = "test_user"
    claims = {"role": "user"}
    
    access_token, _ = auth_manager.generate_jwt(user_id, claims)
    
    # Validate valid token
    payload = auth_manager.validate_token(access_token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["role"] == "user"
    
    # Validate invalid token
    invalid_token = "invalid.token.here"
    assert auth_manager.validate_token(invalid_token) is None

def test_revoke_token(auth_manager):
    user_id = "test_user"
    access_token, _ = auth_manager.generate_jwt(user_id, {})
    
    # Token should be valid initially
    assert auth_manager.validate_token(access_token) is not None
    
    # Revoke token
    auth_manager.revoke_token(access_token)
    
    # Token should be invalid after revocation
    assert auth_manager.validate_token(access_token) is None

def test_refresh_access_token(auth_manager):
    user_id = "test_user"
    _, refresh_token = auth_manager.generate_jwt(user_id, {})
    
    # Generate new access token
    new_access_token = auth_manager.refresh_access_token(refresh_token)
    assert new_access_token is not None
    
    # Verify new access token
    payload = auth_manager.validate_token(new_access_token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    
    # Try refreshing with invalid token
    assert auth_manager.refresh_access_token("invalid.token") is None

def test_password_hashing(auth_manager):
    password = "secure_password123"
    
    # Hash password
    hashed = auth_manager.hash_password(password)
    assert hashed != password
    
    # Verify correct password
    assert auth_manager.verify_password(password, hashed) is True
    
    # Verify incorrect password
    assert auth_manager.verify_password("wrong_password", hashed) is False

def test_token_expiry(auth_manager):
    # Create config with very short expiry
    config = AuthConfig(
        secret_key="test_key",
        token_expiry=timedelta(seconds=1),
        refresh_token_expiry=timedelta(seconds=1),
        allowed_providers=[AuthProvider.INTERNAL]
    )
    manager = AuthManager(config)
    
    access_token, _ = manager.generate_jwt("test_user", {})
    
    # Token should be valid initially
    assert manager.validate_token(access_token) is not None
    
    # Wait for token to expire
    time.sleep(2)
    
    # Token should be invalid after expiry
    assert manager.validate_token(access_token) is None 