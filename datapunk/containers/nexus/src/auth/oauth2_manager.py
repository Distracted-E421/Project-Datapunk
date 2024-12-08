from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional
import httpx
from .nexus_auth_manager import AuthManager

class OAuthProvider(Enum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"

@dataclass
class OAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]
    provider: OAuthProvider
    auth_url: str
    token_url: str
    userinfo_url: str

class OAuth2Manager:
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self._providers: Dict[OAuthProvider, OAuthConfig] = {}
        self._http_client = httpx.AsyncClient()
        
    def register_provider(self, config: OAuthConfig):
        """Register an OAuth provider configuration."""
        self._providers[config.provider] = config
        
    def get_auth_url(self, provider: OAuthProvider, state: str) -> str:
        """Generate authorization URL for the specified provider."""
        if provider not in self._providers:
            raise ValueError(f"Provider {provider} not registered")
            
        config = self._providers[provider]
        params = {
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "scope": " ".join(config.scopes),
            "response_type": "code",
            "state": state
        }
        
        # Add provider-specific parameters
        if provider == OAuthProvider.GOOGLE:
            params["access_type"] = "offline"
            params["prompt"] = "consent"
            
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{config.auth_url}?{query}"
        
    async def exchange_code(self, provider: OAuthProvider, code: str) -> Dict:
        """Exchange authorization code for access token."""
        if provider not in self._providers:
            raise ValueError(f"Provider {provider} not registered")
            
        config = self._providers[provider]
        data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "redirect_uri": config.redirect_uri,
            "code": code,
            "grant_type": "authorization_code"
        }
        
        async with self._http_client as client:
            response = await client.post(config.token_url, data=data)
            response.raise_for_status()
            return response.json()
            
    async def get_user_info(self, provider: OAuthProvider, access_token: str) -> Dict:
        """Get user information from provider."""
        if provider not in self._providers:
            raise ValueError(f"Provider {provider} not registered")
            
        config = self._providers[provider]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with self._http_client as client:
            response = await client.get(config.userinfo_url, headers=headers)
            response.raise_for_status()
            return response.json()
            
    async def handle_oauth_callback(self, provider: OAuthProvider, code: str) -> tuple[str, str]:
        """Handle OAuth callback and return JWT tokens."""
        # Exchange code for tokens
        token_response = await self.exchange_code(provider, code)
        access_token = token_response["access_token"]
        
        # Get user info
        user_info = await self.get_user_info(provider, access_token)
        
        # Extract user ID and claims based on provider
        if provider == OAuthProvider.GOOGLE:
            user_id = user_info["sub"]
            claims = {
                "email": user_info["email"],
                "name": user_info["name"],
                "provider": provider.value
            }
        elif provider == OAuthProvider.MICROSOFT:
            user_id = user_info["id"]
            claims = {
                "email": user_info["userPrincipalName"],
                "name": user_info["displayName"],
                "provider": provider.value
            }
        else:  # Generic provider
            user_id = str(user_info.get("id") or user_info.get("sub"))
            claims = {
                "provider": provider.value,
                **{k: v for k, v in user_info.items() if isinstance(v, (str, int, bool))}
            }
            
        # Generate JWT tokens
        return self.auth_manager.generate_jwt(user_id, claims) 