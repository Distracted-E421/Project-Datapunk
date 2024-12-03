import pytest
from datetime import timedelta
import httpx
import jwt
from src.nexus.auth.oauth2_manager import OAuth2Manager, OAuthProvider, OAuthConfig
from src.nexus.auth.auth_manager import AuthManager, AuthConfig, AuthProvider

@pytest.fixture
def auth_manager():
    config = AuthConfig(
        secret_key="test_secret_key",
        token_expiry=timedelta(minutes=15),
        refresh_token_expiry=timedelta(days=7),
        allowed_providers=[AuthProvider.OAUTH2]
    )
    return AuthManager(config)

@pytest.fixture
def oauth2_manager(auth_manager):
    return OAuth2Manager(auth_manager)

@pytest.fixture
def google_config():
    return OAuthConfig(
        client_id="google_client_id",
        client_secret="google_client_secret",
        redirect_uri="http://localhost:8000/auth/callback/google",
        scopes=["openid", "email", "profile"],
        provider=OAuthProvider.GOOGLE,
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo"
    )

def test_register_provider(oauth2_manager, google_config):
    oauth2_manager.register_provider(google_config)
    assert oauth2_manager._providers[OAuthProvider.GOOGLE] == google_config

def test_get_auth_url(oauth2_manager, google_config):
    oauth2_manager.register_provider(google_config)
    state = "random_state"
    url = oauth2_manager.get_auth_url(OAuthProvider.GOOGLE, state)
    
    assert "https://accounts.google.com/o/oauth2/v2/auth" in url
    assert "client_id=google_client_id" in url
    assert "redirect_uri=http://localhost:8000/auth/callback/google" in url
    assert "scope=openid+email+profile" in url
    assert f"state={state}" in url
    assert "access_type=offline" in url
    assert "prompt=consent" in url

def test_get_auth_url_invalid_provider(oauth2_manager):
    with pytest.raises(ValueError, match="Provider OAuthProvider.GOOGLE not registered"):
        oauth2_manager.get_auth_url(OAuthProvider.GOOGLE, "state")

@pytest.mark.asyncio
async def test_exchange_code(oauth2_manager, google_config, monkeypatch):
    oauth2_manager.register_provider(google_config)
    
    # Mock httpx post response
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            
        def raise_for_status(self):
            pass
            
        def json(self):
            return {
                "access_token": "mock_access_token",
                "token_type": "Bearer",
                "expires_in": 3600
            }
    
    async def mock_post(*args, **kwargs):
        return MockResponse()
        
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    
    token_response = await oauth2_manager.exchange_code(OAuthProvider.GOOGLE, "test_code")
    assert token_response["access_token"] == "mock_access_token"

@pytest.mark.asyncio
async def test_get_user_info(oauth2_manager, google_config, monkeypatch):
    oauth2_manager.register_provider(google_config)
    
    # Mock httpx get response
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            
        def raise_for_status(self):
            pass
            
        def json(self):
            return {
                "sub": "123456789",
                "email": "test@example.com",
                "name": "Test User",
                "picture": "https://example.com/photo.jpg"
            }
    
    async def mock_get(*args, **kwargs):
        return MockResponse()
        
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)
    
    user_info = await oauth2_manager.get_user_info(OAuthProvider.GOOGLE, "mock_access_token")
    assert user_info["sub"] == "123456789"
    assert user_info["email"] == "test@example.com"
    assert user_info["name"] == "Test User"

@pytest.mark.asyncio
async def test_handle_oauth_callback(oauth2_manager, google_config, monkeypatch):
    oauth2_manager.register_provider(google_config)
    
    # Mock exchange_code response
    async def mock_exchange_code(*args, **kwargs):
        return {"access_token": "mock_access_token"}
        
    # Mock get_user_info response
    async def mock_get_user_info(*args, **kwargs):
        return {
            "sub": "123456789",
            "email": "test@example.com",
            "name": "Test User"
        }
        
    monkeypatch.setattr(oauth2_manager, "exchange_code", mock_exchange_code)
    monkeypatch.setattr(oauth2_manager, "get_user_info", mock_get_user_info)
    
    access_token, refresh_token = await oauth2_manager.handle_oauth_callback(
        OAuthProvider.GOOGLE, "test_code"
    )
    
    # Verify tokens
    access_payload = jwt.decode(
        access_token, 
        oauth2_manager.auth_manager.config.secret_key, 
        algorithms=["HS256"]
    )
    assert access_payload["sub"] == "123456789"
    assert access_payload["email"] == "test@example.com"
    assert access_payload["name"] == "Test User"
    assert access_payload["provider"] == "google" 