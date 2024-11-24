"""
Key rotation management for API keys.

This module implements a comprehensive API key rotation system that follows security 
best practices including:
- Automated rotation based on key age and suspicious usage patterns
- Configurable overlap periods to prevent service disruption during rotation
- Emergency rotation capabilities for security incidents
- Audit trail maintenance through rotation history
- Service notification system for coordinated updates

Architecture Notes:
- Uses async/await for non-blocking operations
- Integrates with external services via dependency injection
- Implements defense-in-depth through multiple rotation triggers

Security Considerations:
- Enforces minimum rotation intervals to prevent DoS via excessive rotations
- Supports emergency rotations with shortened overlap periods
- Maintains key history for audit purposes
"""

from typing import Dict, Optional, TYPE_CHECKING, List, Any
import structlog
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .manager import APIKeyManager
from .types import KeyID, KeyRotationResult
from .notifications import KeyNotifier, KeyEventType
from ..core.exceptions import AuthError

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....cache import CacheClient
    from ....messaging import MessageBroker

logger = structlog.get_logger()

class RotationReason(Enum):
    """
    Categorizes the trigger for key rotation to support audit trails and metrics.
    
    SCHEDULED: Normal rotation based on key age
    EMERGENCY: Immediate rotation due to security concerns
    POLICY_CHANGE: Rotation required due to policy updates (e.g., key strength requirements)
    MANUAL: User-initiated rotation
    AUTOMATED: System-initiated based on anomaly detection
    """

@dataclass
class RotationConfig:
    """
    Configuration parameters for key rotation behavior.
    
    Note: These defaults align with NIST 800-57 recommendations for cryptographic
    key lifetime management. Adjust based on specific security requirements.
    
    WARNING: Reducing overlap_period increases risk of service disruption during rotation.
    """
    max_age: timedelta = timedelta(days=90)
    overlap_period: timedelta = timedelta(days=7)
    min_rotation_interval: timedelta = timedelta(days=1)
    emergency_overlap: timedelta = timedelta(hours=1)
    retain_history: int = 5
    notify_before: timedelta = timedelta(days=14)

class KeyRotationManager:
    """
    Orchestrates API key rotation while maintaining service availability.
    
    Design Principles:
    - Atomic operations where possible to prevent partial rotations
    - Graceful degradation during dependency failures
    - Observable operations via metrics and logging
    
    Dependencies:
    - APIKeyManager: Core key CRUD operations
    - CacheClient: Temporary state management
    - MetricsClient: Operational monitoring
    - MessageBroker: Service notifications
    """
    
    def __init__(self,
                 api_key_manager: APIKeyManager,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient',
                 message_broker: 'MessageBroker',
                 config: RotationConfig):
        self.key_manager = api_key_manager
        self.cache = cache_client
        self.metrics = metrics
        self.broker = message_broker
        self.config = config
        self.notifier = KeyNotifier(message_broker, metrics)
        self.logger = logger.bind(component="key_rotation")
    
    async def check_rotation_needed(self, key_id: KeyID) -> Dict[str, Any]:
        """
        Evaluates if a key requires rotation based on multiple criteria.
        
        Implementation Notes:
        - Prioritizes security (emergency rotation) over scheduled rotation
        - Uses a multi-factor approach combining age and usage patterns
        - Supports proactive rotation notification before expiration
        
        TODO: Consider adding rate-based rotation triggers based on key usage volume
        """
        try:
            key = await self.key_manager.get_key(key_id)
            if not key:
                return {"needs_rotation": False}
            
            now = datetime.utcnow()
            created_at = datetime.fromisoformat(key["created_at"])
            age = now - created_at
            
            # Check age-based rotation
            if age >= self.config.max_age:
                return {
                    "needs_rotation": True,
                    "reason": RotationReason.SCHEDULED,
                    "urgency": "high",
                    "time_until_rotation": timedelta(0)
                }
            
            # Check usage patterns
            usage_patterns = await self._analyze_usage_patterns(key_id)
            if usage_patterns["suspicious_activity"]:
                return {
                    "needs_rotation": True,
                    "reason": RotationReason.EMERGENCY,
                    "urgency": "high",
                    "time_until_rotation": timedelta(0)
                }
            
            # Check upcoming scheduled rotation
            time_until_max_age = self.config.max_age - age
            if time_until_max_age <= self.config.notify_before:
                return {
                    "needs_rotation": True,
                    "reason": RotationReason.SCHEDULED,
                    "urgency": "medium",
                    "time_until_rotation": time_until_max_age
                }
            
            return {"needs_rotation": False}
            
        except Exception as e:
            self.logger.error("rotation_check_failed",
                            key_id=key_id,
                            error=str(e))
            raise AuthError(f"Failed to check rotation status: {str(e)}")
    
    async def rotate_key(self,
                        key_id: KeyID,
                        reason: RotationReason,
                        rotated_by: str,
                        emergency: bool = False) -> KeyRotationResult:
        """
        Performs key rotation with zero-downtime using overlap periods.
        
        Critical Path:
        1. Validate rotation timing to prevent abuse
        2. Create new key while maintaining old key
        3. Set up overlap period for graceful transition
        4. Notify dependent services
        
        FIXME: Add rollback mechanism for failed rotations
        
        Security Note: Emergency rotations use shortened overlap periods to
        minimize exposure window while maintaining service availability.
        """
        try:
            # Get existing key
            old_key = await self.key_manager.get_key(key_id)
            if not old_key:
                raise AuthError(f"Key {key_id} not found")
            
            # Validate rotation timing
            await self._validate_rotation_timing(key_id)
            
            # Create new key
            new_key = await self.key_manager.create_key(
                service=old_key["service"],
                policy=old_key["policy"],
                created_by=f"rotation:{rotated_by}",
                metadata={
                    "rotated_from": key_id,
                    "rotation_reason": reason.value,
                    "rotation_date": datetime.utcnow().isoformat()
                }
            )
            
            # Set up overlap period
            overlap_period = (self.config.emergency_overlap 
                            if emergency 
                            else self.config.overlap_period)
            
            await self._setup_overlap_period(old_key, overlap_period)
            
            # Store rotation history
            await self._store_rotation_history(old_key, new_key, reason)
            
            # Notify about rotation
            await self.notifier.notify(
                KeyEventType.ROTATED,
                key_id,
                old_key["service"],
                {
                    "reason": reason.value,
                    "rotated_by": rotated_by,
                    "emergency": emergency,
                    "new_key_id": new_key["key_id"],
                    "overlap_ends": (datetime.utcnow() + overlap_period).isoformat()
                }
            )
            
            # Update metrics
            self.metrics.increment(
                "key_rotations",
                {
                    "reason": reason.value,
                    "emergency": str(emergency).lower(),
                    "service": old_key["service"]
                }
            )
            
            return {
                "success": True,
                "old_key_id": key_id,
                "new_key_id": new_key["key_id"],
                "overlap_ends": datetime.utcnow() + overlap_period,
                "reason": reason.value
            }
            
        except Exception as e:
            self.logger.error("key_rotation_failed",
                            key_id=key_id,
                            error=str(e))
            raise AuthError(f"Key rotation failed: {str(e)}")
    
    async def _validate_rotation_timing(self, key_id: str) -> None:
        """
        Prevents rotation abuse through rate limiting.
        
        Note: This is a critical security control to prevent:
        - DoS through excessive rotations
        - Resource exhaustion
        - Audit log flooding
        """
        last_rotation = await self._get_last_rotation(key_id)
        if last_rotation:
            time_since_rotation = datetime.utcnow() - last_rotation
            if time_since_rotation < self.config.min_rotation_interval:
                raise AuthError(
                    f"Minimum rotation interval not met. "
                    f"Please wait {self.config.min_rotation_interval - time_since_rotation}"
                )
    
    async def _analyze_usage_patterns(self, key_id: str) -> Dict[str, Any]:
        """
        Detects suspicious key usage patterns warranting emergency rotation.
        
        TODO: Implement actual analysis including:
        - Unusual access patterns
        - Geographic anomalies
        - Volume spikes
        - Error rate monitoring
        """
        # Implementation would analyze metrics and logs
        # This is a placeholder
        return {"suspicious_activity": False}
    
    async def _setup_overlap_period(self, old_key: Dict, overlap_period: timedelta) -> None:
        """
        Configures graceful transition period between old and new keys.
        
        Implementation Note: This method appears twice in the file - should be
        deduplicated to prevent maintenance issues.
        """
        overlap_expiry = datetime.utcnow() + overlap_period
        await self.key_manager.update_expiry(old_key["key_id"], overlap_expiry)
    
    async def _store_rotation_history(self, old_key: Dict, new_key: Dict, reason: RotationReason) -> None:
        """Store rotation history for old key."""
        # Implementation would store rotation history in a database
        # This is a placeholder
        pass
    
    async def _get_last_rotation(self, key_id: str) -> Optional[datetime]:
        """Get the last rotation date for a key."""
        # Implementation would retrieve the last rotation date from a database
        # This is a placeholder
        return None 