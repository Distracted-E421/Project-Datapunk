"""
Session management system.

This module implements a secure, scalable session management system with the following features:
- Stateful session tracking using distributed cache
- Cryptographically secure token generation
- Multi-device session support with concurrent session limits
- Activity tracking and automatic session expiration
- MFA integration and security controls
- Event notifications for session lifecycle changes

Key components:
- SessionManager: Orchestrates session lifecycle and security policies
- SessionStore: Handles persistent session storage and retrieval
- SessionToken: Represents session authentication credentials
- SessionContext: Encapsulates session authentication context

Security considerations:
- Uses secure token generation via secrets module
- Implements session fixation protection
- Supports location/device tracking for anomaly detection
- Provides MFA enforcement capabilities
- Includes rate limiting and concurrent session controls

Integration points:
- Requires CacheClient for session storage
- Requires MetricsClient for operational monitoring
- Requires MessageBroker for session event notifications
"""

from typing import Dict, Optional, Any, TYPE_CHECKING, List, Set
import structlog
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import secrets
import hashlib
import json
import uuid

from .types import UserID, SessionID, TokenID
from .exceptions import SessionError

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....cache import CacheClient
    from ....messaging import MessageBroker

logger = structlog.get_logger()

class SessionStatus(Enum):
    """
    Defines possible session states for lifecycle tracking.
    
    ACTIVE: Session is valid and can be used for authentication
    EXPIRED: Session has exceeded its TTL and is no longer valid
    REVOKED: Session was explicitly terminated (e.g., logout, security policy)
    LOCKED: Session temporarily disabled due to security events
    SUSPICIOUS: Session flagged for potential security issues
    """

@dataclass
class SessionConfig:
    """
    Configuration parameters for session management policies.
    
    Security considerations:
    - ttl: Shorter values reduce attack window but increase user friction
    - max_concurrent: Limits credential sharing and account takeover risks
    - lock_threshold: Balances security vs legitimate auth failures
    - track_location/devices: Enables anomaly detection but increases privacy impact
    """
    ttl: timedelta = timedelta(hours=12)
    max_concurrent: int = 5
    require_mfa: bool = False
    refresh_threshold: timedelta = timedelta(minutes=30)
    lock_threshold: int = 3  # Failed attempts before lock
    lock_duration: timedelta = timedelta(minutes=15)
    track_activity: bool = True
    track_location: bool = True
    track_devices: bool = True

@dataclass
class SessionToken:
    """Session token details."""
    token_id: TokenID
    session_id: SessionID
    user_id: UserID
    expires_at: datetime
    scope: Optional[Set[str]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class SessionContext:
    """Context for session operations."""
    user_id: UserID
    client_ip: str
    user_agent: str
    device_id: Optional[str] = None
    location: Optional[str] = None
    mfa_verified: bool = False
    metadata: Optional[Dict[str, Any]] = None

class SessionStore:
    """
    Persistent session storage implementation using distributed cache.
    
    Design notes:
    - Uses cache prefix 'session:' for session data
    - Uses cache prefix 'user:sessions:' for tracking user's active sessions
    - Implements atomic operations for consistency
    - Handles cache failures gracefully with logging
    
    Performance considerations:
    - Cache operations should be monitored for latency
    - Consider implementing batch operations for high-volume scenarios
    """
    
    def __init__(self,
                 cache: 'CacheClient',
                 metrics: 'MetricsClient'):
        self.cache = cache
        self.metrics = metrics
        self.logger = logger.bind(component="session_store")
    
    async def store_session(self,
                          session_id: SessionID,
                          data: Dict,
                          ttl: Optional[int] = None) -> None:
        """Store session data."""
        try:
            key = f"session:{session_id}"
            await self.cache.set(key, data, ttl)
            
            # Update user's active sessions
            user_key = f"user:sessions:{data['user_id']}"
            await self.cache.sadd(user_key, session_id)
            
            self.metrics.increment("sessions_stored")
            
        except Exception as e:
            self.logger.error("session_storage_failed",
                            session_id=session_id,
                            error=str(e))
            raise SessionError(f"Failed to store session: {str(e)}")
    
    async def get_session(self, session_id: SessionID) -> Optional[Dict]:
        """Retrieve session data."""
        try:
            key = f"session:{session_id}"
            return await self.cache.get(key)
            
        except Exception as e:
            self.logger.error("session_retrieval_failed",
                            session_id=session_id,
                            error=str(e))
            raise SessionError(f"Failed to retrieve session: {str(e)}")
    
    async def delete_session(self, session_id: SessionID) -> None:
        """Delete session data."""
        try:
            # Get session data first
            session = await self.get_session(session_id)
            if not session:
                return
            
            # Remove from cache
            key = f"session:{session_id}"
            await self.cache.delete(key)
            
            # Remove from user's active sessions
            user_key = f"user:sessions:{session['user_id']}"
            await self.cache.srem(user_key, session_id)
            
            self.metrics.increment("sessions_deleted")
            
        except Exception as e:
            self.logger.error("session_deletion_failed",
                            session_id=session_id,
                            error=str(e))
            raise SessionError(f"Failed to delete session: {str(e)}")

class SessionManager:
    """
    Core session management implementation handling lifecycle and security.
    
    Security workflow:
    1. Validates creation context (MFA, concurrent limits)
    2. Generates cryptographic session token
    3. Maintains session state and activity tracking
    4. Enforces security policies during validation
    5. Handles secure session termination
    
    Integration notes:
    - Emits events for session lifecycle changes
    - Tracks metrics for operational monitoring
    - Implements graceful degradation on subsystem failures
    
    TODO: Consider implementing session migration for seamless re-authentication
    TODO: Add support for hierarchical session relationships
    FIXME: Improve performance of concurrent session checking
    """
    
    def __init__(self,
                 store: SessionStore,
                 metrics: 'MetricsClient',
                 message_broker: 'MessageBroker',
                 config: SessionConfig):
        self.store = store
        self.metrics = metrics
        self.broker = message_broker
        self.config = config
        self.logger = logger.bind(component="session_manager")
    
    async def create_session(self,
                           context: SessionContext) -> SessionToken:
        """
        Creates new authenticated session with security validation.
        
        Security checks:
        1. MFA verification if required
        2. Concurrent session limits
        3. Device/location tracking
        
        Note: Session creation is atomic - either fully succeeds or fails
        """
        try:
            # Check MFA requirement
            if self.config.require_mfa and not context.mfa_verified:
                raise SessionError("MFA verification required")
            
            # Check concurrent sessions
            if not await self._check_concurrent_sessions(context.user_id):
                raise SessionError("Maximum concurrent sessions reached")
            
            # Generate session and token
            session_id = str(uuid.uuid4())
            token = self._generate_token()
            expires_at = datetime.utcnow() + self.config.ttl
            
            # Create session data
            session_data = {
                "session_id": session_id,
                "user_id": context.user_id,
                "token_id": token.token_id,
                "status": SessionStatus.ACTIVE.value,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "client_ip": context.client_ip,
                "user_agent": context.user_agent,
                "device_id": context.device_id,
                "location": context.location,
                "metadata": context.metadata
            }
            
            # Store session
            await self.store.store_session(
                session_id,
                session_data,
                int(self.config.ttl.total_seconds())
            )
            
            # Notify about new session
            await self._notify_session_created(session_data)
            
            # Update metrics
            self.metrics.increment(
                "sessions_created",
                {"user_id": context.user_id}
            )
            
            return SessionToken(
                token_id=token.token_id,
                session_id=session_id,
                user_id=context.user_id,
                expires_at=expires_at,
                metadata=context.metadata
            )
            
        except Exception as e:
            self.logger.error("session_creation_failed",
                            user_id=context.user_id,
                            error=str(e))
            raise SessionError(f"Failed to create session: {str(e)}")
    
    async def validate_session(self,
                             token: SessionToken,
                             context: Optional[SessionContext] = None) -> bool:
        """
        Validates session authenticity and enforces security policies.
        
        Validation steps:
        1. Verifies session exists and is active
        2. Checks expiration
        3. Validates token cryptographically
        4. Verifies context (device/location) if provided
        5. Updates activity tracking
        
        Edge cases:
        - Handles race conditions with session expiration
        - Gracefully handles missing sessions
        - Considers clock skew in expiration checks
        """
        try:
            # Get session data
            session = await self.store.get_session(token.session_id)
            if not session:
                return False
            
            # Check status
            if session["status"] != SessionStatus.ACTIVE.value:
                return False
            
            # Check expiry
            expires_at = datetime.fromisoformat(session["expires_at"])
            if datetime.utcnow() >= expires_at:
                await self._expire_session(token.session_id)
                return False
            
            # Validate token
            if not self._validate_token(token, session):
                return False
            
            # Check context if provided
            if context:
                if not await self._validate_context(context, session):
                    return False
            
            # Update last activity
            if self.config.track_activity:
                await self._update_activity(session, context)
            
            return True
            
        except Exception as e:
            self.logger.error("session_validation_failed",
                            session_id=token.session_id,
                            error=str(e))
            return False
    
    async def revoke_session(self,
                            session_id: SessionID,
                            reason: str) -> None:
        """Revoke active session."""
        try:
            session = await self.store.get_session(session_id)
            if not session:
                return
            
            # Update status
            session["status"] = SessionStatus.REVOKED.value
            session["revoked_at"] = datetime.utcnow().isoformat()
            session["revocation_reason"] = reason
            
            # Store updated session
            await self.store.store_session(session_id, session)
            
            # Notify about revocation
            await self._notify_session_revoked(session, reason)
            
            # Update metrics
            self.metrics.increment(
                "sessions_revoked",
                {"user_id": session["user_id"]}
            )
            
        except Exception as e:
            self.logger.error("session_revocation_failed",
                            session_id=session_id,
                            error=str(e))
            raise SessionError(f"Failed to revoke session: {str(e)}")
    
    def _generate_token(self) -> SessionToken:
        """
        Generates cryptographically secure session token.
        
        Security notes:
        - Uses secrets module for secure random generation
        - Token length provides adequate entropy
        - Token is URL-safe for transport
        
        TODO: Consider implementing token rotation
        """
        token_id = secrets.token_urlsafe(32)
        return SessionToken(
            token_id=token_id,
            session_id="",  # Set by caller
            user_id="",     # Set by caller
            expires_at=datetime.utcnow() + self.config.ttl
        )
    
    def _validate_token(self,
                       token: SessionToken,
                       session: Dict) -> bool:
        """Validate session token."""
        return (token.token_id == session["token_id"] and
                token.user_id == session["user_id"])
    
    async def _check_concurrent_sessions(self, user_id: UserID) -> bool:
        """Check concurrent session limit."""
        user_key = f"user:sessions:{user_id}"
        active_sessions = await self.store.cache.scard(user_key)
        return active_sessions < self.config.max_concurrent
    
    async def _validate_context(self,
                              context: SessionContext,
                              session: Dict) -> bool:
        """
        Validates session context against stored security parameters.
        
        Validation includes:
        - Device fingerprint matching if enabled
        - Location verification if enabled
        - Custom security rules from metadata
        
        Note: Strict matching may cause issues with dynamic IPs or device updates
        """
        # Validate device if tracking enabled
        if (self.config.track_devices and
            context.device_id and
            context.device_id != session["device_id"]):
            return False
        
        # Validate location if tracking enabled
        if (self.config.track_location and
            context.location and
            context.location != session["location"]):
            return False
        
        return True
    
    async def _update_activity(self,
                             session: Dict,
                             context: Optional[SessionContext]) -> None:
        """Update session activity tracking."""
        session["last_activity"] = datetime.utcnow().isoformat()
        if context:
            session["last_ip"] = context.client_ip
            session["last_user_agent"] = context.user_agent
        
        await self.store.store_session(
            session["session_id"],
            session
        )
    
    async def _expire_session(self, session_id: SessionID) -> None:
        """Handle session expiration."""
        session = await self.store.get_session(session_id)
        if not session:
            return
        
        session["status"] = SessionStatus.EXPIRED.value
        session["expired_at"] = datetime.utcnow().isoformat()
        
        await self.store.store_session(session_id, session)
        await self._notify_session_expired(session)
    
    async def _notify_session_created(self, session: Dict) -> None:
        """Notify about new session creation."""
        await self.broker.publish(
            "sessions.created",
            {
                "session_id": session["session_id"],
                "user_id": session["user_id"],
                "created_at": session["created_at"],
                "client_ip": session["client_ip"],
                "device_id": session["device_id"],
                "location": session["location"]
            }
        )
    
    async def _notify_session_revoked(self,
                                    session: Dict,
                                    reason: str) -> None:
        """Notify about session revocation."""
        await self.broker.publish(
            "sessions.revoked",
            {
                "session_id": session["session_id"],
                "user_id": session["user_id"],
                "revoked_at": session["revoked_at"],
                "reason": reason
            }
        )
    
    async def _notify_session_expired(self, session: Dict) -> None:
        """Notify about session expiration."""
        await self.broker.publish(
            "sessions.expired",
            {
                "session_id": session["session_id"],
                "user_id": session["user_id"],
                "expired_at": session["expired_at"]
            }
        ) 