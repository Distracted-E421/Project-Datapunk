from typing import Dict, List, Optional, TYPE_CHECKING
import structlog
import secrets
import hashlib
from datetime import datetime, timedelta

from .policies import KeyPolicy, KeyType
from .validation import KeyValidator, KeyValidationConfig
from .types import KeyID, KeyHash, KeySecret
from ..core.exceptions import AuthError
from .notifications import KeyNotifier, KeyEventType

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....cache import CacheClient
    from ..audit.audit import AuditLogger

logger = structlog.get_logger()

class APIKeyManager:
    """
    Manages the complete lifecycle of API keys including creation, validation, revocation, and policy updates.
    
    This manager implements a secure key management system with the following features:
    - Secure key generation and hashing
    - Policy-based access control
    - Audit logging
    - Metrics tracking
    - Cache-based storage with optional TTL
    - Event notifications for key lifecycle changes
    
    Security considerations:
    - Keys are never stored in plain text, only their hashes are persisted
    - All operations are audited and metrics are collected
    - Optional TTL support for automatic key expiration
    """
    
    def __init__(self,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient',
                 audit_logger: 'AuditLogger',
                 validator: KeyValidator,
                 key_ttl: Optional[timedelta] = None):
        """
        Initialize the API Key Manager with required dependencies.
        
        NOTE: The key_ttl parameter determines the lifetime of all keys created by this manager.
        If not specified, keys will not expire automatically.
        """
        self.cache = cache_client
        self.metrics = metrics
        self.audit = audit_logger
        self.validator = validator
        self.key_ttl = key_ttl
        self.logger = logger.bind(component="api_key_manager")
    
    async def create_key(self,
                        service: str,
                        policy: KeyPolicy,
                        created_by: str,
                        metadata: Optional[Dict] = None) -> Dict:
        """
        Create and store a new API key with associated policy and metadata.
        
        Security workflow:
        1. Generate random key and compute its hash
        2. Validate key against policy requirements
        3. Store key data with hash (never the plain text key)
        4. Audit the creation event
        5. Update usage metrics
        
        IMPORTANT: This is the only time the plain text key is available.
        It must be securely transmitted to the client and cannot be retrieved later.
        """
        try:
            # Generate key
            key_secret = self._generate_key()
            key_hash = self._hash_key(key_secret)
            key_id = f"key_{datetime.utcnow().timestamp()}"
            
            # Validate key and policy
            validation_result = await self.validator.validate_key(
                key_secret,
                policy
            )
            
            if not validation_result["valid"]:
                raise AuthError(
                    f"Invalid key configuration: {validation_result['issues']}"
                )
            
            # Store key data
            key_data = {
                "key_id": key_id,
                "key_hash": key_hash,
                "service": service,
                "policy": vars(policy),
                "created_at": datetime.utcnow().isoformat(),
                "created_by": created_by,
                "metadata": metadata
            }
            
            if self.key_ttl:
                key_data["expires_at"] = (
                    datetime.utcnow() + self.key_ttl
                ).isoformat()
            
            await self._store_key(key_id, key_data)
            
            # Audit key creation
            await self.audit.log_event(
                "api_key_created",
                {
                    "key_id": key_id,
                    "service": service,
                    "created_by": created_by,
                    "policy_type": policy.type.value
                }
            )
            
            # Update metrics
            self.metrics.increment(
                "api_keys_created",
                {"service": service, "type": policy.type.value}
            )
            
            return {
                "key_id": key_id,
                "key": key_secret,
                "service": service,
                "created_at": key_data["created_at"],
                "expires_at": key_data.get("expires_at")
            }
            
        except Exception as e:
            self.logger.error("key_creation_failed",
                            service=service,
                            error=str(e))
            raise AuthError(f"Failed to create API key: {str(e)}")
    
    def _generate_key(self) -> str:
        """
        Generate a cryptographically secure random API key.
        
        Uses secrets.token_urlsafe for:
        - URL-safe character set
        - Cryptographic randomness
        - 32 bytes of entropy (resulting in ~43 characters)
        """
        return secrets.token_urlsafe(32)
    
    def _hash_key(self, key: str) -> str:
        """
        Hash API key for secure storage using SHA-256.
        
        NOTE: This is a one-way operation. The original key cannot be recovered
        from this hash, which is why we only return the plain text key once
        during creation.
        """
        return hashlib.sha256(key.encode()).hexdigest()
    
    async def _store_key(self, key_id: str, key_data: Dict) -> None:
        """
        Store key data in the cache with optional TTL.
        
        NOTE: The cache implementation should guarantee:
        - Atomic operations
        - Durability of key data
        - Proper handling of TTL expiration
        """
        await self.cache.set(
            f"api_key:{key_id}",
            key_data,
            ttl=int(self.key_ttl.total_seconds()) if self.key_ttl else None
        )
    
    async def revoke_key(self,
                        key_id: str,
                        reason: str,
                        revoked_by: str) -> bool:
        """
        Permanently revoke an API key.
        
        Security implications:
        - Revocation is immediate and permanent
        - The key remains in storage with revoked status for audit purposes
        - All services must check key status before accepting it
        
        NOTE: Consider implementing a grace period or scheduled revocation
        for production-critical keys to prevent immediate service disruption.
        """
        try:
            key_data = await self._get_key(key_id)
            if not key_data:
                raise AuthError(f"Key {key_id} not found")
            
            # Update key status
            key_data["status"] = "revoked"
            key_data["revoked_at"] = datetime.utcnow().isoformat()
            key_data["revoked_by"] = revoked_by
            key_data["revocation_reason"] = reason
            
            # Store updated key data
            await self._store_key(key_id, key_data)
            
            # Notify about revocation
            await self.notifier.notify(
                KeyEventType.REVOKED,
                key_id,
                key_data["service"],
                {
                    "reason": reason,
                    "revoked_by": revoked_by
                }
            )
            
            # Audit event
            await self.audit.log_event(
                "api_key_revoked",
                {
                    "key_id": key_id,
                    "service": key_data["service"],
                    "revoked_by": revoked_by,
                    "reason": reason
                }
            )
            
            # Update metrics
            self.metrics.increment(
                "api_keys_revoked",
                {"service": key_data["service"]}
            )
            
            return True
            
        except Exception as e:
            self.logger.error("key_revocation_failed",
                            key_id=key_id,
                            error=str(e))
            raise AuthError(f"Failed to revoke key: {str(e)}")
    
    async def update_policy(self,
                          key_id: str,
                          new_policy: KeyPolicy,
                          updated_by: str) -> Dict:
        """
        Update the policy associated with an existing API key.
        
        IMPORTANT: Policy updates take effect immediately. Ensure that:
        1. The new policy is compatible with existing integrations
        2. All affected services are prepared for the policy change
        3. The update is performed during a low-traffic period
        
        The old policy is preserved in audit logs for tracking changes.
        """
        try:
            key_data = await self._get_key(key_id)
            if not key_data:
                raise AuthError(f"Key {key_id} not found")
            
            # Validate new policy
            validation_result = await self.validator.validate_key(
                key_data["key_hash"],
                new_policy
            )
            
            if not validation_result["valid"]:
                raise AuthError(
                    f"Invalid policy configuration: {validation_result['issues']}"
                )
            
            # Update policy
            old_policy = key_data["policy"]
            key_data["policy"] = vars(new_policy)
            key_data["updated_at"] = datetime.utcnow().isoformat()
            key_data["updated_by"] = updated_by
            
            # Store updated key data
            await self._store_key(key_id, key_data)
            
            # Notify about policy update
            await self.notifier.notify(
                KeyEventType.POLICY_UPDATED,
                key_id,
                key_data["service"],
                {
                    "old_policy": old_policy,
                    "new_policy": vars(new_policy),
                    "updated_by": updated_by
                }
            )
            
            # Audit event
            await self.audit.log_event(
                "api_key_policy_updated",
                {
                    "key_id": key_id,
                    "service": key_data["service"],
                    "updated_by": updated_by,
                    "old_policy": old_policy,
                    "new_policy": vars(new_policy)
                }
            )
            
            return {
                "key_id": key_id,
                "service": key_data["service"],
                "policy": vars(new_policy),
                "updated_at": key_data["updated_at"]
            }
            
        except Exception as e:
            self.logger.error("policy_update_failed",
                            key_id=key_id,
                            error=str(e))
            raise AuthError(f"Failed to update policy: {str(e)}")
    
    async def _get_key(self, key_id: str) -> Optional[Dict]:
        """
        Retrieve key data from cache.
        
        IMPORTANT: This method only returns metadata and the key hash.
        The original API key is never stored or retrievable.
        """
        return await self.cache.get(f"api_key:{key_id}")