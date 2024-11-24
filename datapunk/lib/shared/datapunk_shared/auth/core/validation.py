from typing import Dict, Optional, TYPE_CHECKING
import structlog
from dataclasses import dataclass

from ..types import ValidationResult, ValidationContext
from ...exceptions import ValidationError

if TYPE_CHECKING:
    from ...monitoring import MetricsClient

logger = structlog.get_logger()

@dataclass
class ValidationConfig:
    """Configuration for validation rules."""
    max_role_depth: int = 5
    max_policies_per_role: int = 20
    max_conditions_per_policy: int = 10
    validate_parent_roles: bool = True
    strict_mode: bool = False

class CoreValidator:
    """Validates core auth components."""
    
    def __init__(self,
                 config: ValidationConfig,
                 metrics: 'MetricsClient'):
        self.config = config
        self.metrics = metrics
        self.logger = logger.bind(component="core_validation")
    
    async def validate_role(self,
                          role: 'Role',
                          context: Optional[ValidationContext] = None) -> ValidationResult:
        """Validate role configuration."""
        try:
            issues = []
            
            # Check role depth
            if role.parent_roles and len(role.parent_roles) > self.config.max_role_depth:
                issues.append(f"Role depth exceeds maximum of {self.config.max_role_depth}")
            
            # Check policies
            if len(role.policies) > self.config.max_policies_per_role:
                issues.append(f"Number of policies exceeds maximum of {self.config.max_policies_per_role}")
            
            # Check policy conditions
            for policy in role.policies:
                if policy.conditions and len(policy.conditions) > self.config.max_conditions_per_policy:
                    issues.append(f"Number of conditions exceeds maximum of {self.config.max_conditions_per_policy}")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues
            }
            
        except Exception as e:
            self.logger.error("role_validation_failed",
                            error=str(e))
            raise ValidationError(f"Role validation failed: {str(e)}") 