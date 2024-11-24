from typing import Dict, List, Optional, Set
import structlog
from dataclasses import dataclass
from enum import Enum
from .key_policies_extended import AdvancedKeyPolicy, ResourceType, CompliancePolicy
from ..exceptions import ValidationError

logger = structlog.get_logger()

class ValidationSeverity(Enum):
    """Severity levels for policy validation."""
    ERROR = "error"        # Must be fixed
    WARNING = "warning"    # Should be reviewed
    INFO = "info"         # Informational only

@dataclass
class ValidationResult:
    """Result of policy validation."""
    valid: bool
    issues: List[Dict]
    recommendations: List[Dict]

class PolicyValidator:
    """Validates API key policies for correctness and security."""
    
    def __init__(self):
        self.logger = logger.bind(component="policy_validator")
    
    def validate_policy(self, policy: AdvancedKeyPolicy) -> ValidationResult:
        """Validate a key policy configuration."""
        issues = []
        recommendations = []
        
        try:
            # Validate basic settings
            self._validate_rate_limits(policy, issues, recommendations)
            self._validate_resource_access(policy, issues, recommendations)
            self._validate_security_settings(policy, issues, recommendations)
            self._validate_monitoring_settings(policy, issues, recommendations)
            
            # Validate compliance if required
            if policy.compliance:
                self._validate_compliance(policy.compliance, issues, recommendations)
            
            # Check for potential security risks
            self._check_security_risks(policy, issues, recommendations)
            
            # Validate resource quotas
            if policy.quota:
                self._validate_quotas(policy, issues, recommendations)
            
            # Check time windows if configured
            if policy.time_windows:
                self._validate_time_windows(policy, issues, recommendations)
            
            valid = not any(i["severity"] == ValidationSeverity.ERROR.value 
                          for i in issues)
            
            return ValidationResult(valid=valid,
                                 issues=issues,
                                 recommendations=recommendations)
            
        except Exception as e:
            self.logger.error("policy_validation_failed",
                            error=str(e))
            raise ValidationError(f"Policy validation failed: {str(e)}")
    
    def _validate_rate_limits(self,
                            policy: AdvancedKeyPolicy,
                            issues: List[Dict],
                            recommendations: List[Dict]):
        """Validate rate limiting configuration."""
        if policy.rate_limit <= 0:
            issues.append({
                "severity": ValidationSeverity.ERROR.value,
                "message": "Rate limit must be positive",
                "field": "rate_limit",
                "value": policy.rate_limit
            })
        
        if policy.burst_limit > policy.rate_limit:
            issues.append({
                "severity": ValidationSeverity.WARNING.value,
                "message": "Burst limit exceeds rate limit",
                "field": "burst_limit",
                "value": policy.burst_limit
            })
        
        if policy.rate_limit > 10000:
            recommendations.append({
                "type": "performance",
                "message": "Consider lower rate limit for better resource management",
                "current_value": policy.rate_limit,
                "suggested_value": 10000
            })
    
    def _validate_resource_access(self,
                                policy: AdvancedKeyPolicy,
                                issues: List[Dict],
                                recommendations: List[Dict]):
        """Validate resource access configuration."""
        if policy.allowed_resources and policy.denied_resources:
            # Check for conflicts
            conflicts = policy.allowed_resources & policy.denied_resources
            if conflicts:
                issues.append({
                    "severity": ValidationSeverity.ERROR.value,
                    "message": "Resource appears in both allowed and denied lists",
                    "resources": list(conflicts)
                })
        
        if not policy.allowed_resources and not policy.denied_resources:
            recommendations.append({
                "type": "security",
                "message": "Consider explicitly defining resource access"
            })
    
    def _validate_security_settings(self,
                                  policy: AdvancedKeyPolicy,
                                  issues: List[Dict],
                                  recommendations: List[Dict]):
        """Validate security-related settings."""
        if not policy.encryption_required:
            issues.append({
                "severity": ValidationSeverity.WARNING.value,
                "message": "Encryption should be required for security"
            })
        
        if policy.type.value in ["admin", "service"] and not policy.require_mfa:
            recommendations.append({
                "type": "security",
                "message": "Consider enabling MFA for privileged access"
            })
    
    def _validate_monitoring_settings(self,
                                    policy: AdvancedKeyPolicy,
                                    issues: List[Dict],
                                    recommendations: List[Dict]):
        """Validate monitoring configuration."""
        if policy.monitoring_level == "minimal":
            recommendations.append({
                "type": "observability",
                "message": "Consider higher monitoring level for better visibility"
            })
        
        if not policy.alert_threshold and policy.type.value in ["admin", "service"]:
            recommendations.append({
                "type": "monitoring",
                "message": "Consider setting alert thresholds for privileged access"
            })
    
    def _validate_compliance(self,
                           compliance: CompliancePolicy,
                           issues: List[Dict],
                           recommendations: List[Dict]):
        """Validate compliance requirements."""
        if not compliance.encryption_required:
            issues.append({
                "severity": ValidationSeverity.ERROR.value,
                "message": "Encryption required for compliance",
                "field": "compliance.encryption_required"
            })
        
        if compliance.audit_level != "full":
            issues.append({
                "severity": ValidationSeverity.WARNING.value,
                "message": "Full audit logging recommended for compliance",
                "field": "compliance.audit_level"
            })
    
    def _check_security_risks(self,
                            policy: AdvancedKeyPolicy,
                            issues: List[Dict],
                            recommendations: List[Dict]):
        """Check for potential security risks."""
        if policy.type.value == "admin":
            if not policy.ip_whitelist:
                issues.append({
                    "severity": ValidationSeverity.WARNING.value,
                    "message": "IP whitelist recommended for admin access"
                })
            
            if not policy.circuit_breaker:
                recommendations.append({
                    "type": "security",
                    "message": "Consider adding circuit breaker for admin access"
                })
    
    def _validate_quotas(self,
                        policy: AdvancedKeyPolicy,
                        issues: List[Dict],
                        recommendations: List[Dict]):
        """Validate resource quotas."""
        if policy.quota.requests_per_day <= 0:
            issues.append({
                "severity": ValidationSeverity.ERROR.value,
                "message": "Daily request quota must be positive",
                "field": "quota.requests_per_day"
            })
        
        if policy.quota.concurrent_connections > 100:
            recommendations.append({
                "type": "performance",
                "message": "Consider lower concurrent connection limit",
                "current_value": policy.quota.concurrent_connections,
                "suggested_value": 100
            })
    
    def _validate_time_windows(self,
                             policy: AdvancedKeyPolicy,
                             issues: List[Dict],
                             recommendations: List[Dict]):
        """Validate time window restrictions."""
        for window in policy.time_windows:
            if window.start_time >= window.end_time:
                issues.append({
                    "severity": ValidationSeverity.ERROR.value,
                    "message": "Invalid time window",
                    "details": {
                        "start": window.start_time.isoformat(),
                        "end": window.end_time.isoformat()
                    }
                })
            
            if not window.days:
                issues.append({
                    "severity": ValidationSeverity.ERROR.value,
                    "message": "Time window must specify allowed days"
                }) 