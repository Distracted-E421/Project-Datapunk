from datetime import datetime, timedelta
import jwt
from typing import Dict, Optional
from dataclasses import dataclass
import secrets
import hashlib
from enum import Enum

class AuthProvider(Enum):
    INTERNAL = "internal"
    OAUTH2 = "oauth2"
    
@dataclass
class AuthConfig:
    secret_key: str
    token_expiry: timedelta
    refresh_token_expiry: timedelta
    allowed_providers: list[AuthProvider]
    oauth2_settings: Optional[Dict] = None

class AuthManager:
    def __init__(self, config: AuthConfig):
        self.config = config
        self._token_blacklist = set()
        
    def generate_jwt(self, user_id: str, claims: Dict) -> tuple[str, str]:
        """Generate JWT access and refresh tokens."""
        now = datetime.utcnow()
        
        # Access token
        access_payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + self.config.token_expiry,
            "type": "access",
            **claims
        }
        access_token = jwt.encode(access_payload, self.config.secret_key, algorithm="HS256")
        
        # Refresh token
        refresh_payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + self.config.refresh_token_expiry,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)
        }
        refresh_token = jwt.encode(refresh_payload, self.config.secret_key, algorithm="HS256")
        
        return access_token, refresh_token
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token and return claims if valid."""
        try:
            if token in self._token_blacklist:
                return None
                
            payload = jwt.decode(token, self.config.secret_key, algorithms=["HS256"])
            
            # Check token type and expiry
            if payload.get("type") not in ["access", "refresh"]:
                return None
                
            if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
                return None
                
            return payload
            
        except jwt.InvalidTokenError:
            return None
            
    def revoke_token(self, token: str):
        """Add token to blacklist."""
        self._token_blacklist.add(token)
        
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token using refresh token."""
        payload = self.validate_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
            
        user_id = payload["sub"]
        new_access_token, _ = self.generate_jwt(user_id, {})
        return new_access_token
        
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
        
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return self.hash_password(password) == hashed 