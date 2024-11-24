from typing import Dict, Optional, TYPE_CHECKING, List
import structlog
from dataclasses import dataclass
import re

from .policies import KeyPolicy, KeyType
from .types import KeyValidationResult
from ..core.exceptions import ValidationError

if TYPE_CHECKING:
    from ....monitoring import MetricsClient

logger = structlog.get_logger()

@dataclass
class KeyValidationConfig:
    """Configuration for key validation."""
    min_key_length: int = 32
    max_key_length: int = 64
    require_ip_whitelist: bool = True
    require_path_restrictions: bool = True
    allowed_key_types: Optional[set[KeyType]] = None
    strict_mode: bool = True

class KeyValidator:
    """Validates API keys and their policies."""
    
    def __init__(self,
                 config: KeyValidationConfig,
                 metrics: 'MetricsClient'):
        self.config = config
        self.metrics = metrics
        self.logger = logger.bind(component="key_validation")
    
    async def validate_key(self,
                          key: str,
                          policy: KeyPolicy,
                          context: Optional[Dict] = None) -> KeyValidationResult:
        """Validate API key and its policy."""
        try:
            issues = []
            warnings = []
            
            # Validate key format
            if not self._validate_key_format(key):
                issues.append("Invalid key format")
            
            # Validate key length
            if len(key) < self.config.min_key_length:
                issues.append(f"Key too short (min {self.config.min_key_length})")
            elif len(key) > self.config.max_key_length:
                issues.append(f"Key too long (max {self.config.max_key_length})")
            
            # Validate key type
            if (self.config.allowed_key_types and 
                policy.type not in self.config.allowed_key_types):
                issues.append(f"Key type {policy.type} not allowed")
            
            # Validate policy restrictions
            policy_issues = await self._validate_policy_restrictions(policy)
            issues.extend(policy_issues)
            
            # Update metrics
            self.metrics.increment(
                "key_validations",
                {
                    "type": policy.type.value,
                    "has_issues": str(bool(issues)).lower(),
                    "has_warnings": str(bool(warnings)).lower()
                }
            )
            
            return {
                "valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings
            }
            
        except Exception as e:
            self.logger.error("key_validation_failed",
                            error=str(e))
            raise ValidationError(f"Key validation failed: {str(e)}")
    
    def _validate_key_format(self, key: str) -> bool:
        """Validate key format using regex."""
        # Key format: alphanumeric with optional dashes
        key_pattern = r'^[A-Za-z0-9\-]+$'
        return bool(re.match(key_pattern, key))
    
    async def _validate_policy_restrictions(self,
                                         policy: KeyPolicy) -> List[str]:
        """Validate policy restrictions."""
        issues = []
        
        # Check IP whitelist
        if (self.config.require_ip_whitelist and 
            not policy.ip_whitelist and 
            policy.type != KeyType.ADMIN):
            issues.append("IP whitelist required for non-admin keys")
        
        # Check path restrictions
        if (self.config.require_path_restrictions and 
            not policy.allowed_paths and 
            policy.type != KeyType.ADMIN):
            issues.append("Path restrictions required for non-admin keys")
        
        # Check rate limits
        if policy.rate_limit <= 0:
            issues.append("Rate limit must be positive")
        
        if policy.burst_limit > policy.rate_limit:
            issues.append("Burst limit cannot exceed rate limit")
        
        return issues