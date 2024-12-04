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
    """Configuration for key validation.
    
    Defines security requirements and constraints for API key validation:
    - Key length boundaries to prevent weak or unwieldy keys
    - Security policy requirements for non-admin keys
    - Configurable key type restrictions
    - Strict mode flag for enforcing all validations
    """
    min_key_length: int = 32  # Minimum length ensures sufficient entropy
    max_key_length: int = 64  # Maximum length prevents DoS via oversized keys
    require_ip_whitelist: bool = True  # Enforces IP-based access control
    require_path_restrictions: bool = True  # Enforces API endpoint restrictions
    allowed_key_types: Optional[set[KeyType]] = None  # If set, restricts key types
    strict_mode: bool = True  # When True, enforces all validation rules

class KeyValidator:
    """Validates API keys and their associated security policies.
    
    Performs comprehensive validation of API keys including:
    - Key format and length validation
    - Policy-based restrictions (IP whitelist, path access, rate limits)
    - Key type validation against allowed types
    
    Integrates with metrics system for monitoring validation patterns and issues.
    """
    
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
        """Validate API key and its policy.
        
        Performs multi-stage validation process:
        1. Key format and length validation
        2. Key type verification against allowed types
        3. Policy restrictions validation
        
        Args:
            key: The API key string to validate
            policy: Associated security policy for the key
            context: Optional contextual data for validation (reserved for future use)
            
        Returns:
            KeyValidationResult containing validation status and any issues/warnings
            
        Raises:
            ValidationError: If validation process encounters an unexpected error
        """
        try:
            issues = []
            warnings = []
            
            # Basic key format and length validations
            if not self._validate_key_format(key):
                issues.append("Invalid key format")
            
            if len(key) < self.config.min_key_length:
                issues.append(f"Key too short (min {self.config.min_key_length})")
            elif len(key) > self.config.max_key_length:
                issues.append(f"Key too long (max {self.config.max_key_length})")
            
            # Verify key type if restrictions are configured
            if (self.config.allowed_key_types and 
                policy.type not in self.config.allowed_key_types):
                issues.append(f"Key type {policy.type} not allowed")
            
            # Validate policy-specific restrictions
            policy_issues = await self._validate_policy_restrictions(policy)
            issues.extend(policy_issues)
            
            # Track validation metrics for monitoring and alerting
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
        """Validate key format using regex.
        
        Ensures key contains only alphanumeric characters and dashes.
        This format allows for readable keys while maintaining security.
        
        NOTE: Consider extending pattern for additional special characters
        if needed for specific use cases.
        """
        key_pattern = r'^[A-Za-z0-9\-]+$'
        return bool(re.match(key_pattern, key))
    
    async def _validate_policy_restrictions(self,
                                         policy: KeyPolicy) -> List[str]:
        """Validate policy restrictions.
        
        Enforces security policy requirements:
        - IP whitelist for access control (except admin keys)
        - Path restrictions for API access control (except admin keys)
        - Rate limiting constraints to prevent abuse
        
        Admin keys are exempt from certain restrictions as they're intended
        for trusted system operations.
        
        Returns:
            List of validation issues found in the policy
        """
        issues = []
        
        # IP whitelist required for non-admin keys for access control
        if (self.config.require_ip_whitelist and 
            not policy.ip_whitelist and 
            policy.type != KeyType.ADMIN):
            issues.append("IP whitelist required for non-admin keys")
        
        # Path restrictions required for non-admin keys for API security
        if (self.config.require_path_restrictions and 
            not policy.allowed_paths and 
            policy.type != KeyType.ADMIN):
            issues.append("Path restrictions required for non-admin keys")
        
        # Validate rate limiting configuration
        if policy.rate_limit <= 0:
            issues.append("Rate limit must be positive")
        
        # Ensure burst limit doesn't exceed base rate limit
        if policy.burst_limit > policy.rate_limit:
            issues.append("Burst limit cannot exceed rate limit")
        
        return issues