from typing import Optional, Dict, List
import time
import uuid
import structlog
from datetime import datetime, timedelta
from ..cache import CacheClient
from ..monitoring import MetricsClient
from dataclasses import dataclass

logger = structlog.get_logger()

@dataclass
class APIKeyConfig:
    """Configuration for API key management."""
    ttl: int = 86400 * 30  # 30 days
    max_keys_per_service: int = 5
    key_prefix: str = "pk_"
    cache_prefix: str = "apikey:"

class APIKeyManager:
    """Manages API key lifecycle and validation."""
    
    def __init__(self, 
                 cache_client: CacheClient,
                 metrics: MetricsClient,
                 config: APIKeyConfig = APIKeyConfig()):
        self.cache = cache_client
        self.metrics = metrics
        self.config = config
        self.logger = logger.bind(component="api_keys")
    
    async def create_key(self,
                        service_name: str,
                        scopes: List[str],
                        metadata: Dict = None) -> Dict:
        """Create new API key."""
        try:
            # Check key limit
            existing_keys = await self.list_keys(service_name)
            if len(existing_keys) >= self.config.max_keys_per_service:
                raise ValueError(f"Maximum keys reached for {service_name}")
            
            # Generate key
            key_id = str(uuid.uuid4())
            key = f"{self.config.key_prefix}{key_id}"
            
            key_data = {
                "id": key_id,
                "service": service_name,
                "scopes": scopes,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat(),
                "last_used": None
            }
            
            # Store key data
            cache_key = f"{self.config.cache_prefix}{key_id}"
            await self.cache.set(cache_key, key_data, self.config.ttl)
            
            self.metrics.increment("api_key_created", {"service": service_name})
            self.logger.info("api_key_created",
                           service=service_name,
                           key_id=key_id)
            
            return {"key": key, **key_data}
            
        except Exception as e:
            self.logger.error("api_key_creation_failed",
                            service=service_name,
                            error=str(e))
            raise
    
    async def validate_key(self,
                          key: str,
                          required_scopes: List[str] = None) -> Optional[Dict]:
        """Validate API key and check scopes."""
        try:
            if not key.startswith(self.config.key_prefix):
                return None
                
            key_id = key[len(self.config.key_prefix):]
            cache_key = f"{self.config.cache_prefix}{key_id}"
            
            key_data = await self.cache.get(cache_key)
            if not key_data:
                return None
            
            # Check scopes if required
            if required_scopes:
                if not all(scope in key_data["scopes"] for scope in required_scopes):
                    return None
            
            # Update last used
            key_data["last_used"] = datetime.utcnow().isoformat()
            await self.cache.set(cache_key, key_data, self.config.ttl)
            
            self.metrics.increment("api_key_validated",
                                 {"service": key_data["service"]})
            
            return key_data
            
        except Exception as e:
            self.logger.error("api_key_validation_failed",
                            error=str(e))
            return None
    
    async def revoke_key(self, key_id: str) -> bool:
        """Revoke API key."""
        try:
            cache_key = f"{self.config.cache_prefix}{key_id}"
            key_data = await self.cache.get(cache_key)
            
            if not key_data:
                return False
            
            await self.cache.delete(cache_key)
            
            self.metrics.increment("api_key_revoked",
                                 {"service": key_data["service"]})
            self.logger.info("api_key_revoked",
                           key_id=key_id,
                           service=key_data["service"])
            
            return True
            
        except Exception as e:
            self.logger.error("api_key_revocation_failed",
                            key_id=key_id,
                            error=str(e))
            return False
    
    async def list_keys(self, service_name: str) -> List[Dict]:
        """List all keys for a service."""
        try:
            pattern = f"{self.config.cache_prefix}*"
            all_keys = await self.cache.scan(pattern)
            
            service_keys = []
            for cache_key in all_keys:
                key_data = await self.cache.get(cache_key)
                if key_data and key_data["service"] == service_name:
                    service_keys.append(key_data)
            
            return service_keys
            
        except Exception as e:
            self.logger.error("api_key_listing_failed",
                            service=service_name,
                            error=str(e))
            return [] 