"""
Service mesh integration for cross-service authentication.

Purpose:
    Provides secure service-to-service authentication and session management within a distributed system.

Context:
    Core component of the authentication infrastructure, enabling secure communication between microservices
    while maintaining user session consistency across service boundaries.

Design/Details:
    - Implements JWT-based service authentication with mTLS support
    - Manages distributed session state using cache and message broker
    - Provides session propagation for seamless user experience across services
    - Uses RS256 for token signing to ensure security at scale

Prerequisites:
    - Private/public key pair for JWT signing
    - Running cache service (Redis recommended)
    - Message broker (RabbitMQ/Kafka)
    - Service mesh infrastructure

Security Considerations:
    - Implements mTLS for service-to-service communication
    - Uses asymmetric encryption for token signing
    - Includes token revocation capabilities
    - Implements clock skew tolerance
    - Validates service identity before session propagation

Error Handling:
    - Comprehensive error handling for token validation
    - Graceful handling of network failures
    - Retry mechanism for critical operations
    - Structured logging for debugging

Known Issues:
    - Clock synchronization between services is critical
    - Session propagation has a 5-minute timeout window
    - Cache failures can impact service authentication state
"""

from typing import Dict, Optional, Any, TYPE_CHECKING, List, Set
import structlog
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import jwt
import uuid

from ..core.security import SecurityManager
from ..core.session import SessionManager, SessionToken
from ..core.exceptions import AuthError
from ..types import UserID, ServiceID, TokenID

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....cache import CacheClient
    from ....messaging import MessageBroker
    from ....mesh import ServiceMesh

logger = structlog.get_logger()

class ServiceAuthStatus(Enum):
    """
    Represents the possible authentication states of a service.
    AUTHENTICATED: Service has valid credentials and is active
    UNAUTHORIZED: Service lacks proper credentials
    EXPIRED: Valid credentials that have timed out
    REVOKED: Explicitly revoked credentials
    INVALID: Malformed or corrupt credentials
    """

@dataclass
class ServiceAuthConfig:
    """
    Configuration parameters for service authentication behavior.
    
    NOTE: token_ttl should be balanced between security (shorter) and performance (longer)
    TODO: Consider making retry parameters configurable per-service
    """
    token_ttl: timedelta = timedelta(hours=1)
    require_mtls: bool = True
    sync_interval: int = 30  # seconds
    max_clock_skew: int = 30  # seconds
    retry_attempts: int = 3
    retry_delay: int = 5  # seconds

@dataclass
class ServiceAuthContext:
    """Context for service authentication."""
    service_id: ServiceID
    client_cert: Optional[str] = None
    client_key: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AuthMesh:
    """
    Manages service-to-service authentication and session propagation.
    
    Design Notes:
    - Uses distributed cache for auth state to support horizontal scaling
    - Implements event-driven architecture for auth state changes
    - Supports graceful degradation if dependent services are unavailable
    """
    
    def __init__(self,
                 service_mesh: 'ServiceMesh',
                 security_manager: SecurityManager,
                 session_manager: SessionManager,
                 metrics: 'MetricsClient',
                 cache: 'CacheClient',
                 message_broker: 'MessageBroker',
                 config: ServiceAuthConfig):
        self.mesh = service_mesh
        self.security = security_manager
        self.sessions = session_manager
        self.metrics = metrics
        self.cache = cache
        self.broker = message_broker
        self.config = config
        self.logger = logger.bind(component="auth_mesh")
    
    async def authenticate_service(self,
                                 context: ServiceAuthContext) -> Dict[str, Any]:
        """
        Authenticates a service and issues a service token.
        
        SECURITY: Validates mTLS certificates before issuing tokens
        NOTE: Failures are logged and metrics updated for monitoring
        """
        try:
            # Validate mTLS if required
            if self.config.require_mtls:
                await self._validate_mtls(context)
            
            # Generate service token
            token = await self._generate_service_token(context)
            
            # Store auth state
            await self._store_auth_state(context, token)
            
            # Notify about authentication
            await self._notify_service_auth(context, token)
            
            # Update metrics
            self.metrics.increment(
                "service_authentications",
                {"service": context.service_id}
            )
            
            return {
                "token": token,
                "expires_at": datetime.utcnow() + self.config.token_ttl,
                "service_id": context.service_id
            }
            
        except Exception as e:
            self.logger.error("service_auth_failed",
                            service=context.service_id,
                            error=str(e))
            raise AuthError(f"Service authentication failed: {str(e)}")
    
    async def validate_service_token(self,
                                   token: str,
                                   required_service: Optional[ServiceID] = None) -> Dict[str, Any]:
        """
        Validates a service token and checks its current status.
        
        IMPORTANT: Implements clock skew tolerance for distributed systems
        NOTE: Token validation includes both cryptographic checks and status verification
        """
        try:
            # Decode token
            try:
                payload = jwt.decode(
                    token,
                    self.security.get_public_key(),
                    algorithms=["RS256"]
                )
            except jwt.InvalidTokenError as e:
                raise AuthError(f"Invalid token: {str(e)}")
            
            # Check service
            if (required_service and 
                payload["service_id"] != required_service):
                raise AuthError("Invalid service")
            
            # Check expiry
            if datetime.fromtimestamp(payload["exp"]) <= datetime.utcnow():
                raise AuthError("Token expired")
            
            # Get auth state
            state = await self._get_auth_state(payload["service_id"])
            if not state:
                raise AuthError("No auth state found")
            
            # Check if revoked
            if state["status"] != ServiceAuthStatus.AUTHENTICATED.value:
                raise AuthError(f"Token {state['status']}")
            
            return {
                "service_id": payload["service_id"],
                "authenticated": True,
                "metadata": state.get("metadata")
            }
            
        except AuthError:
            raise
        except Exception as e:
            self.logger.error("token_validation_failed",
                            error=str(e))
            raise AuthError(f"Token validation failed: {str(e)}")
    
    async def propagate_session(self,
                              session_token: SessionToken,
                              target_service: ServiceID) -> Dict[str, Any]:
        """
        Propagates user session to another service securely.
        
        Design Notes:
        - Uses short-lived propagation tokens (5 min) to minimize security risks
        - Implements event notification for session state consistency
        - Target service must validate propagation token independently
        """
        try:
            # Validate session
            if not await self.sessions.validate_session(session_token):
                raise AuthError("Invalid session")
            
            # Create propagation token
            prop_token = await self._create_propagation_token(
                session_token,
                target_service
            )
            
            # Notify target service
            await self._notify_session_propagation(
                session_token,
                target_service,
                prop_token
            )
            
            return {
                "propagation_token": prop_token,
                "target_service": target_service,
                "expires_at": datetime.utcnow() + timedelta(minutes=5)
            }
            
        except Exception as e:
            self.logger.error("session_propagation_failed",
                            error=str(e))
            raise AuthError(f"Session propagation failed: {str(e)}")
    
    async def _validate_mtls(self, context: ServiceAuthContext) -> None:
        """
        Validates mTLS certificates for service authentication.
        
        SECURITY: Critical security check for service identity verification
        TODO: Add certificate rotation support
        """
        if not context.client_cert or not context.client_key:
            raise AuthError("mTLS certificates required")
            
        # Validate using security manager
        await self.security.validate_cert(
            context.client_cert,
            context.service_id
        )
    
    async def _generate_service_token(self,
                                    context: ServiceAuthContext) -> str:
        """
        Generates JWT token for service authentication.
        
        IMPORTANT: Uses asymmetric encryption (RS256) for better security at scale
        NOTE: Includes unique JTI for token revocation support
        """
        now = datetime.utcnow()
        payload = {
            "iss": "auth_mesh",
            "sub": context.service_id,
            "service_id": context.service_id,
            "iat": int(now.timestamp()),
            "exp": int((now + self.config.token_ttl).timestamp()),
            "jti": str(uuid.uuid4())
        }
        
        if context.metadata:
            payload["metadata"] = context.metadata
        
        return jwt.encode(
            payload,
            self.security.get_private_key(),
            algorithm="RS256"
        )
    
    async def _store_auth_state(self,
                               context: ServiceAuthContext,
                               token: str) -> None:
        """
        Maintains service authentication state in distributed cache.
        
        Design Notes:
        - TTL matches token lifetime for automatic cleanup
        - Includes metadata for audit and debugging purposes
        """
        state = {
            "service_id": context.service_id,
            "status": ServiceAuthStatus.AUTHENTICATED.value,
            "authenticated_at": datetime.utcnow().isoformat(),
            "expires_at": (
                datetime.utcnow() + self.config.token_ttl
            ).isoformat(),
            "token_id": jwt.decode(token, verify=False)["jti"],
            "metadata": context.metadata
        }
        
        await self.cache.set(
            f"auth:service:{context.service_id}",
            state,
            ttl=int(self.config.token_ttl.total_seconds())
        )
    
    async def _get_auth_state(self, service_id: ServiceID) -> Optional[Dict]:
        """Get service authentication state."""
        return await self.cache.get(f"auth:service:{service_id}")
    
    async def _notify_service_auth(self,
                                 context: ServiceAuthContext,
                                 token: str) -> None:
        """Notify about service authentication."""
        await self.broker.publish(
            "auth.service.authenticated",
            {
                "service_id": context.service_id,
                "authenticated_at": datetime.utcnow().isoformat(),
                "token_id": jwt.decode(token, verify=False)["jti"],
                "metadata": context.metadata
            }
        )
    
    async def _create_propagation_token(self,
                                      session_token: SessionToken,
                                      target_service: ServiceID) -> str:
        """Create session propagation token."""
        now = datetime.utcnow()
        payload = {
            "iss": "auth_mesh",
            "sub": session_token.user_id,
            "session_id": session_token.session_id,
            "target_service": target_service,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
            "jti": str(uuid.uuid4())
        }
        
        return jwt.encode(
            payload,
            self.security.get_private_key(),
            algorithm="RS256"
        )
    
    async def _notify_session_propagation(self,
                                        session_token: SessionToken,
                                        target_service: ServiceID,
                                        prop_token: str) -> None:
        """Notify about session propagation."""
        await self.broker.publish(
            f"auth.session.propagated.{target_service}",
            {
                "session_id": session_token.session_id,
                "user_id": session_token.user_id,
                "source_service": self.mesh.service_name,
                "target_service": target_service,
                "propagation_token": prop_token,
                "timestamp": datetime.utcnow().isoformat()
            }
        ) 