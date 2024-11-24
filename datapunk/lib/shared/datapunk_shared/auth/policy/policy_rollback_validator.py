from typing import Dict, List, Optional
import structlog
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from ..api_keys.policies_extended import AdvancedKeyPolicy, ResourceType
from ...exceptions import RollbackError, ValidationError

logger = structlog.get_logger()

class RollbackRisk(Enum):
    """
    Risk classification for policy rollbacks aligned with NIST risk management framework.
    Used to determine approval requirements and implementation strategies.
    """
    LOW = "low"           # Configuration changes without security impact
    MEDIUM = "medium"     # Changes affecting non-critical security controls
    HIGH = "high"         # Changes to critical security controls
    CRITICAL = "critical" # Changes violating compliance requirements or security boundaries

@dataclass
class RollbackValidationResult:
    """
    Comprehensive validation outcome for policy rollback operations.
    Captures both immediate impacts and recommended mitigations.
    """
    is_valid: bool           # Whether rollback can proceed safely
    risk_level: RollbackRisk # Assessed impact level
    breaking_changes: List[str]  # Changes that could break existing integrations
    warnings: List[str]      # Non-blocking issues requiring attention
    recommendations: List[str]  # Suggested mitigations or alternatives

class PolicyRollbackValidator:
    """
    Validates security policy rollbacks for safety and compliance.
    
    Performs multi-dimensional analysis of policy changes including:
    - Resource access modifications
    - Security control impacts
    - Compliance requirement violations
    - Performance implications
    
    NOTE: This validator assumes policies are well-formed and already validated
    for syntax and structure. Use PolicyValidator first if needed.
    """
    
    def __init__(self, metrics_client):
        """
        Initialize validator with metrics tracking.
        Metrics are used for rollback trend analysis and alerting.
        """
        self.metrics = metrics_client
        self.logger = logger.bind(component="rollback_validator")
    
    async def validate_rollback(self,
                              current_policy: AdvancedKeyPolicy,
                              rollback_policy: AdvancedKeyPolicy,
                              affected_keys: List[str]) -> RollbackValidationResult:
        """
        Comprehensive validation of policy rollback safety.
        
        Performs staged validation across multiple security dimensions:
        1. Resource access changes (permissions)
        2. Security control modifications
        3. Compliance requirement impacts
        4. Performance implications
        
        IMPORTANT: Validation occurs in order of decreasing criticality to fail fast
        on serious issues before checking less critical aspects.
        
        NOTE: Large numbers of affected keys (>1000) automatically elevate risk level
        due to broader blast radius.
        """
        try:
            breaking_changes = []
            warnings = []
            recommendations = []
            
            # Staged validation pipeline
            self._validate_resource_access(
                current_policy,
                rollback_policy,
                breaking_changes,
                warnings
            )
            
            self._validate_security_changes(
                current_policy,
                rollback_policy,
                breaking_changes,
                warnings,
                recommendations
            )
            
            self._validate_compliance_changes(
                current_policy,
                rollback_policy,
                breaking_changes,
                warnings,
                recommendations
            )
            
            self._validate_performance_changes(
                current_policy,
                rollback_policy,
                warnings,
                recommendations
            )
            
            risk_level = self._assess_risk_level(
                breaking_changes,
                warnings,
                affected_keys
            )
            
            # Telemetry for monitoring rollback patterns
            self.logger.info("rollback_validation_complete",
                           risk_level=risk_level.value,
                           breaking_changes=len(breaking_changes),
                           warnings=len(warnings))
            
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
        """
        Validates changes to resource access permissions.
        
        IMPORTANT: Any reduction in resource access is considered a breaking change
        as it may disrupt existing integrations. New restrictions are warnings
        as they only affect future access attempts.
        
        NOTE: Empty resource sets are skipped as they indicate unrestricted access
        """
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
        """
        Validates changes to security controls.
        
        Critical security controls (encryption, MFA) being disabled are breaking changes.
        Secondary controls (IP restrictions, monitoring) generate warnings.
        
        NOTE: Security downgrades always include recommendations for alternatives
        or compensating controls.
        """
        # Core security requirements
        if current.encryption_required and not rollback.encryption_required:
            breaking_changes.append(
                "Rollback removes encryption requirement"
            )
        
        if current.require_mfa and not rollback.require_mfa:
            breaking_changes.append(
                "Rollback removes MFA requirement"
            )
        
        # Secondary controls
        if current.ip_whitelist and not rollback.ip_whitelist:
            warnings.append(
                "Rollback removes IP whitelist restrictions"
            )
        
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
        """
        Validates compliance requirement impacts.
        
        IMPORTANT: Compliance violations are always breaking changes as they may
        affect regulatory status. Reduced controls generate warnings for audit purposes.
        
        NOTE: Early return if either policy lacks compliance settings to avoid
        null reference issues.
        """
        if not current.compliance or not rollback.compliance:
            return
            
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
        """
        Validates performance-related changes.
        
        Reduced limits generate warnings as they may affect service quality.
        Recommendations are provided for maintaining higher limits where feasible.
        
        NOTE: Performance changes never generate breaking changes as they don't
        affect security posture directly.
        """
        if rollback.rate_limit < current.rate_limit:
            warnings.append(
                f"Rollback reduces rate limit from {current.rate_limit} to {rollback.rate_limit}"
            )
        
        if rollback.burst_limit < current.burst_limit:
            warnings.append(
                f"Rollback reduces burst limit from {current.burst_limit} to {rollback.burst_limit}"
            )
        
        if rollback.max_parallel < current.max_parallel:
            recommendations.append(
                f"Consider maintaining higher parallel connection limit of {current.max_parallel}"
            )
    
    def _assess_risk_level(self,
                          breaking_changes: List[str],
                          warnings: List[str],
                          affected_keys: List[str]) -> RollbackRisk:
        """
        Determines overall risk level of rollback operation.
        
        Risk assessment hierarchy:
        1. Breaking changes -> CRITICAL (automatic)
        2. Many warnings or keys -> HIGH
        3. Some warnings or keys -> MEDIUM
        4. Minor changes -> LOW
        
        NOTE: Large scale (>1000 keys) automatically elevates to HIGH risk
        due to potential impact breadth.
        """
        if len(breaking_changes) > 0:
            return RollbackRisk.CRITICAL
            
        if len(warnings) > 3 or len(affected_keys) > 1000:
            return RollbackRisk.HIGH
            
        if len(warnings) > 0 or len(affected_keys) > 100:
            return RollbackRisk.MEDIUM
            
        return RollbackRisk.LOW 