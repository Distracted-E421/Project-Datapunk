from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass
import asyncio
from .api_key_manager import APIKey, KeyType, KeyPolicy
from ..monitoring import MetricsClient
from ..exceptions import AuthError

logger = structlog.get_logger()

@dataclass
class RotationConfig:
    """Configuration for key rotation."""
    rotation_window: timedelta = timedelta(days=30)  # Time before expiry to start rotation
    overlap_period: timedelta = timedelta(days=7)    # Time both keys are valid
    max_key_age: timedelta = timedelta(days=90)      # Maximum key lifetime
    force_rotation: bool = False                     # Force rotation regardless of age
    notification_threshold: timedelta = timedelta(days=7)  # When to notify of upcoming rotation

class KeyRotationManager:
    """Manages automatic key rotation."""
    
    def __init__(self,
                 api_key_manager,
                 metrics: MetricsClient,
                 config: RotationConfig = RotationConfig()):
        self.key_manager = api_key_manager
        self.metrics = metrics
        self.config = config
        self.logger = logger.bind(component="key_rotation")
    
    async def check_rotation_needed(self, key: APIKey) -> bool:
        """Check if key needs rotation."""
        if self.config.force_rotation:
            return True
            
        if not key.expires_at:
            return False
            
        now = datetime.utcnow()
        time_to_expiry = key.expires_at - now
        
        # Check if within rotation window
        return time_to_expiry <= self.config.rotation_window
    
    async def rotate_key(self,
                        key: APIKey,
                        notify: bool = True) -> Tuple[str, APIKey]:
        """Rotate an API key."""
        try:
            # Create new key with same policy but new expiry
            new_expiry = datetime.utcnow() + self.config.max_key_age
            
            new_key_str = await self.key_manager.create_key(
                service=key.service,
                policy=key.policy,
                created_by="system:key_rotation",
                expires_in=self.config.max_key_age,
                metadata={
                    "rotated_from": key.key_id,
                    "rotation_date": datetime.utcnow().isoformat()
                }
            )
            
            # Get new key details
            new_key = await self.key_manager.get_key(new_key_str.split('.')[0])
            
            # Set up overlap period for old key
            await self._setup_overlap_period(key)
            
            # Notify if requested
            if notify:
                await self._notify_rotation(key, new_key)
            
            # Update metrics
            self.metrics.increment(
                "key_rotations_total",
                {"service": key.service, "type": key.policy.type.value}
            )
            
            return new_key_str, new_key
            
        except Exception as e:
            self.logger.error("key_rotation_failed",
                            key_id=key.key_id,
                            error=str(e))
            raise AuthError(f"Key rotation failed: {str(e)}")
    
    async def _setup_overlap_period(self, old_key: APIKey) -> None:
        """Set up overlap period for old key."""
        overlap_expiry = datetime.utcnow() + self.config.overlap_period
        
        # Update old key's expiry
        await self.key_manager.update_expiry(
            old_key.key_id,
            overlap_expiry
        )
    
    async def _notify_rotation(self,
                             old_key: APIKey,
                             new_key: APIKey) -> None:
        """Notify relevant parties of key rotation."""
        # Implementation would depend on notification system
        # This is a placeholder
        self.logger.info("key_rotation_notification",
                        old_key_id=old_key.key_id,
                        new_key_id=new_key.key_id,
                        service=old_key.service)
    
    async def schedule_rotation_check(self) -> None:
        """Schedule periodic rotation checks."""
        while True:
            try:
                # Get all active keys
                keys = await self.key_manager.list_all_keys()
                
                for key in keys:
                    if await self.check_rotation_needed(key):
                        await self.rotate_key(key)
                    elif await self._check_notification_needed(key):
                        await self._notify_upcoming_rotation(key)
                
            except Exception as e:
                self.logger.error("rotation_check_failed",
                                error=str(e))
            
            await asyncio.sleep(3600)  # Check every hour
    
    async def _check_notification_needed(self, key: APIKey) -> bool:
        """Check if rotation notification is needed."""
        if not key.expires_at:
            return False
            
        time_to_rotation = key.expires_at - datetime.utcnow()
        return time_to_rotation <= self.config.notification_threshold
    
    async def _notify_upcoming_rotation(self, key: APIKey) -> None:
        """Notify of upcoming key rotation."""
        self.logger.info("upcoming_key_rotation",
                        key_id=key.key_id,
                        service=key.service,
                        expires_at=key.expires_at.isoformat()) 