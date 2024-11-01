from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from google.oauth2 import id_token
from google.auth.transport import requests
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from pydantic import BaseModel
import aiohttp
from urllib.parse import urlencode
from ..config.oauth_config import get_oauth_settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from db.config.database import get_db
from db.models.user import User

# Initialize settings and security tools
oauth_settings = get_oauth_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
router = APIRouter()

# TODO: These models should be moved to a separate models.py file
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    # TODO: Add additional fields needed for your application
    # provider: str  # "local", "google", or "microsoft"
    # provider_user_id: Optional[str]  # ID from OAuth provider

# Local authentication functions
def verify_password(plain_password, hashed_password):
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate hash from password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create JWT access token
    TODO: In production, consider adding refresh tokens
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        oauth_settings.SECRET_KEY, 
        algorithm=oauth_settings.ALGORITHM
    )
    return encoded_jwt

# TODO: Implement this function to work with your database
async def get_user(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()

# TODO: Implement this function to work with your database
async def create_or_update_user(
    email: str, 
    name: str, 
    provider: str, 
    provider_user_id: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(
            and_(
                User.email == email,
                User.provider == provider
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            email=email,
            full_name=name,
            provider=provider,
            provider_user_id=provider_user_id
        )
        db.add(user)
    else:
        user.full_name = name
        
    await db.commit()
    await db.refresh(user)
    return user

# Local authentication endpoint
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Local authentication endpoint
    TODO: Implement proper user authentication against your database
    """
    user = await get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=oauth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Google OAuth endpoints
@router.get("/auth/google/login")
async def google_login():
    """
    Initiates Google OAuth flow
    Returns URL for frontend to redirect to Google login
    """
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": oauth_settings.GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": " ".join(oauth_settings.GOOGLE_SCOPES),
        "redirect_uri": oauth_settings.GOOGLE_REDIRECT_URI,
        "access_type": "offline",  # Needed to get refresh token
        "prompt": "consent"  # Forces consent screen to always show
    }
    return {"authorization_url": f"{auth_url}?{urlencode(params)}"}

@router.get("/auth/google/callback")
async def google_callback(code: str, request: Request):
    """
    Handles Google OAuth callback
    TODO: Store refresh_token in database for later data access
    """
    token_url = "https://oauth2.googleapis.com/token"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            token_url,
            data={
                "client_id": oauth_settings.GOOGLE_CLIENT_ID,
                "client_secret": oauth_settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": oauth_settings.GOOGLE_REDIRECT_URI,
            },
        ) as response:
            tokens = await response.json()
            
    try:
        idinfo = id_token.verify_oauth2_token(
            tokens["id_token"], 
            requests.Request(), 
            oauth_settings.GOOGLE_CLIENT_ID
        )
        
        # Create or update user in your database
        user = await create_or_update_user(
            email=idinfo["email"],
            name=idinfo["name"],
            provider="google",
            provider_user_id=idinfo["sub"]
        )
        
        # Create access token for your app
        access_token = create_access_token(
            data={"sub": user.id, "provider": "google"}
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Placeholder for Microsoft OAuth integration
@router.get("/auth/microsoft")
async def microsoft_auth():
    # Will implement Microsoft OAuth flow
    pass
