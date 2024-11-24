from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import structlog
import secrets
import hashlib
from dataclasses import dataclass
from enum import Enum
from ..cache import CacheClient
from ..monitoring import MetricsClient
from ..exceptions import AuthError
from .audit import AuditLogger, AuditEvent

logger = structlog.get_logger()

class KeyType(Enum):
    """Types of API keys with different access levels."""
    ADMIN = "admin"          # Full access
    SERVICE = "service"      # Service-to-service
    READ_ONLY = "read_only"  # Read-only access
    LIMITED = "limited"      # Limited scope access

@dataclass
class KeyPolicy:
    """Policy for API key usage and restrictions."""
    type: KeyType
    rate_limit: int = 1000           # Requests per hour
    max_parallel: int = 10           # Max concurrent requests
    ip_whitelist: Set[str] = None    # Allowed IP addresses
    allowed_paths: Set[str] = None   # Allowed API paths
    allowed_methods: Set[str] = None # Allowed HTTP methods

@dataclass
class APIKey:
    """API key details."""
    key_id: str
    key_hash: str
    service: str
    policy: KeyPolicy
    created_at: datetime
    created_by: str
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    metadata: Optional[Dict] = None

class APIKeyManager:
    """Enhanced API key management system."""
    
    def __init__(self,
                 cache_client: CacheClient,
                 metrics: MetricsClient,
                 audit_logger: AuditLogger):
        self.cache = cache_client
        self.metrics = metrics
        self.audit = audit_logger
        self.logger = logger.bind(component="api_key_manager")
    
    async def create_key(self,
                        service: str,
                        policy: KeyPolicy,
                        created_by: str,
                        expires_in: Optional[timedelta] = None,
                        metadata: Optional[Dict] = None) -> tuple[str, str]:
        """Create new API key with policy."""
        try:
            # Generate key parts
            key_id = secrets.token_urlsafe(12)
            key_secret = secrets.token_urlsafe(32)
            key_hash = self._hash_key(key_secret)
            
            # Create key object
            key = APIKey(
                key_id=key_id,
                key_hash=key_hash,
                service=service,
                policy=policy,
                created_at=datetime.utcnow(),
                created_by=created_by,
                expires_at=datetime.utcnow() + expires_in if expires_in else None,
                metadata=metadata
            )
            
            # Store key
            await self._store_key(key)
            
            # Log audit event
            await self.audit.log_event(
                AuditEvent(
                    event_type="api_key_created",
                    actor_id=created_by,
                    resource_type="api_key",
                    resource_id=key_id,
                    action="create",
                    timestamp=datetime.utcnow(),
                    status="success",
                    details={
                        "service": service,
                        "key_type": policy.type.value,
                        "expires_at": key.expires_at.isoformat() if key.expires_at else None
                    }
                )
            )
            
            # Update metrics
            self.metrics.increment(
                "api_key_created",
                {"service": service, "type": policy.type.value}
            )
            
            return f"{key_id}.{key_secret}"
            
        except Exception as e:
            self.logger.error("key_creation_failed",
                            service=service,
                            error=str(e))
            raise AuthError(f"Failed to create API key: {str(e)}")
    
    async def validate_key(self,
                          api_key: str,
                          request_path: str,
                          method: str,
                          client_ip: str) -> Optional[APIKey]:
        """Validate API key and its permissions."""
        try:
            # Split and validate key format
            try:
                key_id, key_secret = api_key.split(".")
            except ValueError:
                return None
            
            # Get key details
            key = await self._get_key(key_id)
            if not key:
                return None
            
            # Verify key hash
            if not self._verify_key(key_secret, key.key_hash):
                return None
            
            # Check expiration
            if key.expires_at and datetime.utcnow() > key.expires_at:
                await self._handle_expired_key(key)
                return None
            
            # Validate policy
            if not await self._validate_policy(key.policy, request_path, method, client_ip):
                return None
            
            # Update usage metrics
            await self._update_usage_metrics(key)
            
            return key
            
        except Exception as e:
            self.logger.error("key_validation_failed",
                            error=str(e))
            return None
    
    async def revoke_key(self,
                        key_id: str,
                        revoked_by: str,
                        reason: str) -> bool:
        """Revoke API key."""
        try:
            key = await self._get_key(key_id)
            if not key:
                return False
            
            # Remove key
            await self.cache.delete(f"apikey:{key_id}")
            
            # Log audit event
            await self.audit.log_event(
                AuditEvent(
                    event_type="api_key_revoked",
                    actor_id=revoked_by,
                    resource_type="api_key",
                    resource_id=key_id,
                    action="revoke",
                    timestamp=datetime.utcnow(),
                    status="success",
                    details={
                        "service": key.service,
                        "reason": reason
                    }
                )
            )
            
            # Update metrics
            self.metrics.increment(
                "api_key_revoked",
                {"service": key.service, "type": key.policy.type.value}
            )
            
            return True
            
        except Exception as e:
            self.logger.error("key_revocation_failed",
                            key_id=key_id,
                            error=str(e))
            return False
    
    def _hash_key(self, key_secret: str) -> str:
        """Hash key secret for storage."""
        return hashlib.sha256(key_secret.encode()).hexdigest()
    
    def _verify_key(self, key_secret: str, key_hash: str) -> bool:
        """Verify key secret against stored hash."""
        return self._hash_key(key_secret) == key_hash
    
    async def _store_key(self, key: APIKey) -> None:
        """Store API key details."""
        await self.cache.set(
            f"apikey:{key.key_id}",
            {
                "key_hash": key.key_hash,
                "service": key.service,
                "policy": vars(key.policy),
                "created_at": key.created_at.isoformat(),
                "created_by": key.created_by,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "metadata": key.metadata
            }
        )
    
    async def _get_key(self, key_id: str) -> Optional[APIKey]:
        """Get API key details."""
        data = await self.cache.get(f"apikey:{key_id}")
        if not data:
            return None
            
        return APIKey(
            key_id=key_id,
            key_hash=data["key_hash"],
            service=data["service"],
            policy=KeyPolicy(**data["policy"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=data["created_by"],
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            metadata=data["metadata"]
        )
    
    async def _validate_policy(self,
                             policy: KeyPolicy,
                             request_path: str,
                             method: str,
                             client_ip: str) -> bool:
        """Validate request against key policy."""
        # Check IP whitelist
        if policy.ip_whitelist and client_ip not in policy.ip_whitelist:
            return False
        
        # Check path restrictions
        if policy.allowed_paths and not any(
            request_path.startswith(path) for path in policy.allowed_paths
        ):
            return False
        
        # Check method restrictions
        if policy.allowed_methods and method not in policy.allowed_methods:
            return False
        
        return True
    
    async def _update_usage_metrics(self, key: APIKey) -> None:
        """Update key usage metrics."""
        now = datetime.utcnow()
        
        # Update last used timestamp
        await self.cache.hset(
            f"apikey:{key.key_id}",
            "last_used",
            now.isoformat()
        )
        
        # Update usage counters
        self.metrics.increment(
            "api_key_usage",
            {
                "service": key.service,
                "type": key.policy.type.value
            }
        )
    
    async def _handle_expired_key(self, key: APIKey) -> None:
        """Handle expired key cleanup."""
        await self.revoke_key(
            key.key_id,
            "system",
            "Key expired"
        ) 