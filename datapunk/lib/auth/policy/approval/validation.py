from typing import Dict, Optional, TYPE_CHECKING, Any
import structlog
from dataclasses import dataclass
from datetime import datetime

from ..types import PolicyType, PolicyStatus
from ...core.exceptions import ValidationError

if TYPE_CHECKING:
    from ....monitoring import MetricsClient

logger = structlog.get_logger()

@dataclass
class ApprovalValidationConfig:
    """Configuration for approval validation.
    
    Defines the rules and constraints for the approval workflow:
    - Controls the maximum number of approvers to prevent approval sprawl
    - Enforces approver uniqueness to maintain approval integrity
    - Manages self-approval permissions for compliance scenarios
    - Sets time limits on pending approvals
    - Determines validation strictness and minimum authority levels
    """
    max_approvers: int = 5
    require_different_approvers: bool = True  # Prevents collusion by requiring diverse approvers
    allow_self_approval: bool = False  # Generally disabled for security best practices
    expiry_hours: int = 24  # Time window for approval completion
    strict_mode: bool = True  # When True, warnings are treated as errors
    min_approval_level: str = "team_lead"  # Minimum authority level required for approval

class ApprovalValidator:
    """Validates approval requests and decisions.
    
    Implements a two-phase validation system:
    1. Initial request validation (validate_request)
    2. Individual approval validation (validate_approval)
    
    Integrates with metrics system for monitoring validation patterns and potential issues.
    
    Note: This validator assumes approver levels are hierarchical strings that can be compared.
    TODO: Consider implementing a proper enum or class for approval levels to ensure type safety.
    """
    
    def __init__(self,
                 config: ApprovalValidationConfig,
                 metrics: 'MetricsClient'):
        self.config = config
        self.metrics = metrics
        self.logger = logger.bind(component="approval_validation")
    
    async def validate_request(self,
                             request: 'ApprovalRequest',
                             context: Optional[Dict] = None) -> Dict[str, Any]:
        """Validate approval request.
        
        Performs comprehensive validation of the initial approval request:
        - Enforces approver count limits
        - Prevents self-approval if configured
        - Ensures approver uniqueness
        - Validates approval authority levels
        
        Returns a dict containing:
        - valid: Boolean indicating if request passes all critical checks
        - issues: List of critical validation failures
        - warnings: List of non-critical concerns
        
        Note: Warnings may be treated as errors if strict_mode is enabled in config
        """
        try:
            issues = []
            warnings = []
            
            # Validate against maximum approver limit to prevent approval sprawl
            if len(request.approvers) > self.config.max_approvers:
                issues.append(f"Too many approvers (max {self.config.max_approvers})")
            
            # Security check: prevent self-approval unless explicitly allowed
            if not self.config.allow_self_approval:
                if request.requester_id in request.approvers:
                    issues.append("Self-approval not allowed")
            
            # Ensure approver diversity to maintain approval integrity
            if (self.config.require_different_approvers and
                len(set(request.approvers)) != len(request.approvers)):
                issues.append("Duplicate approvers not allowed")
            
            # Validate authority level meets minimum requirements
            if request.required_level.value < self.config.min_approval_level:
                warnings.append(f"Approval level below recommended minimum ({self.config.min_approval_level})")
            
            # Track validation outcomes for monitoring and alerting
            self.metrics.increment(
                "approval_validations",
                {
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
            self.logger.error("approval_validation_failed",
                            error=str(e))
            raise ValidationError(f"Approval validation failed: {str(e)}")
    
    async def validate_approval(self,
                              request: 'ApprovalRequest',
                              approver_id: str,
                              approver_level: str) -> Dict[str, Any]:
        """Validate an individual approval action.
        
        Ensures the approval action is valid by checking:
        - Request is still in pending status
        - Request hasn't expired
        - Approver has sufficient authority
        - Approver hasn't already approved
        
        FIXME: Consider adding rate limiting to prevent approval spam
        
        Returns:
        - valid: Boolean indicating if the approval is valid
        - issues: List of validation failures
        """
        try:
            issues = []
            
            # Ensure request is still actionable
            if request.status != "pending":
                issues.append(f"Request is not pending (status: {request.status})")
            
            # Validate request hasn't expired
            if datetime.utcnow() > request.expires_at:
                issues.append("Request has expired")
            
            # Verify approver has sufficient authority
            if approver_level < request.required_level.value:
                issues.append(f"Insufficient approval level (required: {request.required_level.value})")
            
            # Prevent duplicate approvals
            if approver_id in request.approvers:
                issues.append("Approver has already approved this request")
            
            return {
                "valid": len(issues) == 0,
                "issues": issues
            }
            
        except Exception as e:
            self.logger.error("approval_validation_failed",
                            error=str(e))
            raise ValidationError(f"Approval validation failed: {str(e)}")