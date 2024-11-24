from typing import Dict, List, Optional, TYPE_CHECKING
import structlog
from dataclasses import dataclass
from enum import Enum

from ...core.exceptions import ValidationError
from ...types import ValidationResult

if TYPE_CHECKING:
    from ....monitoring import MetricsClient

logger = structlog.get_logger()

class RollbackRisk(Enum):
    """Risk levels for policy rollback."""
    LOW = "low"           # Minor changes, low impact
    MEDIUM = "medium"     # Significant changes, moderate impact
    HIGH = "high"         # Major changes, high impact
    CRITICAL = "critical" # Breaking changes, severe impact

@dataclass
class RollbackValidationResult:
    """Result of rollback validation."""
    is_valid: bool
    risk_level: RollbackRisk
    breaking_changes: List[str]
    warnings: List[str]
    recommendations: List[str]

class RollbackValidator:
    """Validates policy rollbacks for safety and consistency."""
    
    def __init__(self, metrics: 'MetricsClient'):
        self.metrics = metrics
        self.logger = logger.bind(component="rollback_validator")
    
    async def validate_rollback(self,
                              current_policy: Dict,
                              rollback_policy: Dict,
                              affected_keys: List[str]) -> RollbackValidationResult:
        """Validate a policy rollback operation."""
        try:
            breaking_changes = []
            warnings = []
            recommendations = []
            
            # Check resource access changes
            self._validate_resource_access(
                current_policy,
                rollback_policy,
                breaking_changes,
                warnings
            )
            
            # Check security implications
            self._validate_security_changes(
                current_policy,
                rollback_policy,
                breaking_changes,
                warnings,
                recommendations
            )
            
            # Check compliance impact
            self._validate_compliance_changes(
                current_policy,
                rollback_policy,
                breaking_changes,
                warnings,
                recommendations
            )
            
            # Determine risk level
            risk_level = self._assess_risk_level(
                breaking_changes,
                warnings,
                affected_keys
            )
            
            return RollbackValidationResult(
                is_valid=len(breaking_changes) == 0,
                risk_level=risk_level,
                breaking_changes=breaking_changes,
                warnings=warnings,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error("rollback_validation_failed",
                            error=str(e))
            raise ValidationError(f"Rollback validation failed: {str(e)}") 