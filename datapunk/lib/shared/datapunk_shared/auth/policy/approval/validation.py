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
    """Configuration for approval validation."""
    max_approvers: int = 5
    require_different_approvers: bool = True
    allow_self_approval: bool = False
    expiry_hours: int = 24
    strict_mode: bool = True
    min_approval_level: str = "team_lead"

class ApprovalValidator:
    """Validates approval requests and decisions."""
    
    def __init__(self,
                 config: ApprovalValidationConfig,
                 metrics: 'MetricsClient'):
        self.config = config
        self.metrics = metrics
        self.logger = logger.bind(component="approval_validation")
    
    async def validate_request(self,
                             request: 'ApprovalRequest',
                             context: Optional[Dict] = None) -> Dict[str, Any]:
        """Validate approval request."""
        try:
            issues = []
            warnings = []
            
            # Check approvers
            if len(request.approvers) > self.config.max_approvers:
                issues.append(f"Too many approvers (max {self.config.max_approvers})")
            
            # Check for self-approval
            if not self.config.allow_self_approval:
                if request.requester_id in request.approvers:
                    issues.append("Self-approval not allowed")
            
            # Check unique approvers
            if (self.config.require_different_approvers and
                len(set(request.approvers)) != len(request.approvers)):
                issues.append("Duplicate approvers not allowed")
            
            # Check approval level
            if request.required_level.value < self.config.min_approval_level:
                warnings.append(f"Approval level below recommended minimum ({self.config.min_approval_level})")
            
            # Update metrics
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
        """Validate an approval action."""
        try:
            issues = []
            
            # Check request status
            if request.status != "pending":
                issues.append(f"Request is not pending (status: {request.status})")
            
            # Check expiry
            if datetime.utcnow() > request.expires_at:
                issues.append("Request has expired")
            
            # Check approver level
            if approver_level < request.required_level.value:
                issues.append(f"Insufficient approval level (required: {request.required_level.value})")
            
            # Check duplicate approval
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