from typing import Dict, List, Optional
import structlog
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from ..api_keys.policies_extended import AdvancedKeyPolicy, ResourceType
from ...exceptions import RollbackError, ValidationError

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

class PolicyRollbackValidator:
    """Validates policy rollbacks for safety and consistency."""
    
    def __init__(self, metrics_client):
        self.metrics = metrics_client
        self.logger = logger.bind(component="rollback_validator")
    
    async def validate_rollback(self,
                              current_policy: AdvancedKeyPolicy,
                              rollback_policy: AdvancedKeyPolicy,
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
            
            # Check performance impact
            self._validate_performance_changes(
                current_policy,
                rollback_policy,
                warnings,
                recommendations
            )
            
            # Determine risk level
            risk_level = self._assess_risk_level(
                breaking_changes,
                warnings,
                affected_keys
            )
            
            # Log validation results
            self.logger.info("rollback_validation_complete",
                           risk_level=risk_level.value,
                           breaking_changes=len(breaking_changes),
                           warnings=len(warnings))
            
            # Update metrics
            self.metrics.increment(
                "rollback_validations_total",
                {"risk_level": risk_level.value}
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
    
    def _validate_resource_access(self,
                                current: AdvancedKeyPolicy,
                                rollback: AdvancedKeyPolicy,
                                breaking_changes: List[str],
                                warnings: List[str]) -> None:
        """Validate changes in resource access."""
        if current.allowed_resources and rollback.allowed_resources:
            removed_resources = current.allowed_resources - rollback.allowed_resources
            if removed_resources:
                breaking_changes.append(
                    f"Rollback removes access to resources: {removed_resources}"
                )
        
        if current.denied_resources and rollback.denied_resources:
            new_denials = rollback.denied_resources - current.denied_resources
            if new_denials:
                warnings.append(
                    f"Rollback adds new resource restrictions: {new_denials}"
                )
    
    def _validate_security_changes(self,
                                 current: AdvancedKeyPolicy,
                                 rollback: AdvancedKeyPolicy,
                                 breaking_changes: List[str],
                                 warnings: List[str],
                                 recommendations: List[str]) -> None:
        """Validate security-related changes."""
        # Check encryption requirements
        if current.encryption_required and not rollback.encryption_required:
            breaking_changes.append(
                "Rollback removes encryption requirement"
            )
        
        # Check MFA requirements
        if current.require_mfa and not rollback.require_mfa:
            breaking_changes.append(
                "Rollback removes MFA requirement"
            )
        
        # Check IP restrictions
        if current.ip_whitelist and not rollback.ip_whitelist:
            warnings.append(
                "Rollback removes IP whitelist restrictions"
            )
        
        # Check monitoring level
        if (current.monitoring_level == "debug" and 
            rollback.monitoring_level != "debug"):
            recommendations.append(
                "Consider maintaining debug monitoring level"
            )
    
    def _validate_compliance_changes(self,
                                  current: AdvancedKeyPolicy,
                                  rollback: AdvancedKeyPolicy,
                                  breaking_changes: List[str],
                                  warnings: List[str],
                                  recommendations: List[str]) -> None:
        """Validate compliance-related changes."""
        if not current.compliance or not rollback.compliance:
            return
            
        # Check compliance requirements
        if (current.compliance.encryption_required and 
            not rollback.compliance.encryption_required):
            breaking_changes.append(
                "Rollback violates compliance encryption requirements"
            )
        
        if (current.compliance.audit_level == "full" and 
            rollback.compliance.audit_level != "full"):
            warnings.append(
                "Rollback reduces audit logging level"
            )
        
        # Check retention periods
        if (rollback.compliance.retention_period < 
            current.compliance.retention_period):
            warnings.append(
                "Rollback reduces data retention period"
            )
    
    def _validate_performance_changes(self,
                                   current: AdvancedKeyPolicy,
                                   rollback: AdvancedKeyPolicy,
                                   warnings: List[str],
                                   recommendations: List[str]) -> None:
        """Validate performance-related changes."""
        # Check rate limits
        if rollback.rate_limit < current.rate_limit:
            warnings.append(
                f"Rollback reduces rate limit from {current.rate_limit} to {rollback.rate_limit}"
            )
        
        # Check burst limits
        if rollback.burst_limit < current.burst_limit:
            warnings.append(
                f"Rollback reduces burst limit from {current.burst_limit} to {rollback.burst_limit}"
            )
        
        # Check connection limits
        if rollback.max_parallel < current.max_parallel:
            recommendations.append(
                f"Consider maintaining higher parallel connection limit of {current.max_parallel}"
            )
    
    def _assess_risk_level(self,
                          breaking_changes: List[str],
                          warnings: List[str],
                          affected_keys: List[str]) -> RollbackRisk:
        """Assess the risk level of the rollback."""
        if len(breaking_changes) > 0:
            return RollbackRisk.CRITICAL
            
        if len(warnings) > 3 or len(affected_keys) > 1000:
            return RollbackRisk.HIGH
            
        if len(warnings) > 0 or len(affected_keys) > 100:
            return RollbackRisk.MEDIUM
            
        return RollbackRisk.LOW 