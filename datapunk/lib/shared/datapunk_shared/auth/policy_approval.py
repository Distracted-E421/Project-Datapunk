from typing import Dict, List, Optional, Any
import structlog
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from .policy_rollback_validator import RollbackValidationResult, RollbackRisk
from ..exceptions import ApprovalError
from ..monitoring import MetricsClient

logger = structlog.get_logger()

class ApprovalStatus(Enum):
    """Status of approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class ApprovalLevel(Enum):
    """Required approval levels based on risk."""
    NONE = "none"           # No approval needed
    TEAM_LEAD = "team_lead" # Team lead approval
    MANAGER = "manager"     # Manager approval
    DIRECTOR = "director"   # Director approval

@dataclass
class ApprovalRequest:
    """Approval request details."""
    request_id: str
    requester_id: str
    rollback_id: str
    validation_result: RollbackValidationResult
    status: ApprovalStatus
    required_level: ApprovalLevel
    created_at: datetime
    expires_at: datetime
    approvers: List[str]
    metadata: Optional[Dict] = None

class PolicyApprovalManager:
    """Manages approval workflow for policy rollbacks."""
    
    def __init__(self,
                 cache_client,
                 metrics: MetricsClient,
                 approval_ttl: timedelta = timedelta(days=1)):
        self.cache = cache_client
        self.metrics = metrics
        self.approval_ttl = approval_ttl
        self.logger = logger.bind(component="policy_approval")
    
    def _determine_approval_level(self,
                                risk_level: RollbackRisk,
                                breaking_changes: List[str]) -> ApprovalLevel:
        """Determine required approval level based on risk."""
        if risk_level == RollbackRisk.CRITICAL:
            return ApprovalLevel.DIRECTOR
        elif risk_level == RollbackRisk.HIGH:
            return ApprovalLevel.MANAGER
        elif risk_level == RollbackRisk.MEDIUM:
            return ApprovalLevel.TEAM_LEAD
        return ApprovalLevel.NONE
    
    async def create_approval_request(self,
                                    requester_id: str,
                                    rollback_id: str,
                                    validation_result: RollbackValidationResult,
                                    metadata: Optional[Dict] = None) -> ApprovalRequest:
        """Create new approval request."""
        try:
            # Determine required approval level
            required_level = self._determine_approval_level(
                validation_result.risk_level,
                validation_result.breaking_changes
            )
            
            # Create request
            request = ApprovalRequest(
                request_id=f"apr_{datetime.utcnow().timestamp()}",
                requester_id=requester_id,
                rollback_id=rollback_id,
                validation_result=validation_result,
                status=ApprovalStatus.PENDING,
                required_level=required_level,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + self.approval_ttl,
                approvers=[],
                metadata=metadata
            )
            
            # Store request
            await self._store_request(request)
            
            # Update metrics
            self.metrics.increment(
                "approval_requests_created",
                {
                    "risk_level": validation_result.risk_level.value,
                    "approval_level": required_level.value
                }
            )
            
            return request
            
        except Exception as e:
            self.logger.error("approval_request_creation_failed",
                            error=str(e))
            raise ApprovalError(f"Failed to create approval request: {str(e)}")
    
    async def approve_request(self,
                            request_id: str,
                            approver_id: str,
                            approver_level: ApprovalLevel,
                            comments: Optional[str] = None) -> bool:
        """Approve a pending request."""
        try:
            request = await self._get_request(request_id)
            if not request:
                raise ApprovalError(f"Request {request_id} not found")
            
            # Validate request status
            if request.status != ApprovalStatus.PENDING:
                raise ApprovalError(f"Request {request_id} is not pending")
            
            if datetime.utcnow() > request.expires_at:
                request.status = ApprovalStatus.EXPIRED
                await self._store_request(request)
                raise ApprovalError(f"Request {request_id} has expired")
            
            # Validate approver level
            if approver_level.value < request.required_level.value:
                raise ApprovalError("Insufficient approval level")
            
            # Update request
            request.status = ApprovalStatus.APPROVED
            request.approvers.append(approver_id)
            await self._store_request(request)
            
            # Update metrics
            self.metrics.increment(
                "approval_requests_approved",
                {"approval_level": approver_level.value}
            )
            
            return True
            
        except Exception as e:
            self.logger.error("approval_failed",
                            request_id=request_id,
                            error=str(e))
            raise
    
    async def reject_request(self,
                           request_id: str,
                           rejector_id: str,
                           reason: str) -> bool:
        """Reject a pending request."""
        try:
            request = await self._get_request(request_id)
            if not request:
                raise ApprovalError(f"Request {request_id} not found")
            
            if request.status != ApprovalStatus.PENDING:
                raise ApprovalError(f"Request {request_id} is not pending")
            
            # Update request
            request.status = ApprovalStatus.REJECTED
            request.metadata = {
                **(request.metadata or {}),
                "rejected_by": rejector_id,
                "rejection_reason": reason
            }
            await self._store_request(request)
            
            # Update metrics
            self.metrics.increment("approval_requests_rejected")
            
            return True
            
        except Exception as e:
            self.logger.error("rejection_failed",
                            request_id=request_id,
                            error=str(e))
            raise
    
    async def _store_request(self, request: ApprovalRequest) -> None:
        """Store approval request in cache."""
        key = f"approval:request:{request.request_id}"
        await self.cache.set(
            key,
            {
                "request_id": request.request_id,
                "requester_id": request.requester_id,
                "rollback_id": request.rollback_id,
                "validation_result": vars(request.validation_result),
                "status": request.status.value,
                "required_level": request.required_level.value,
                "created_at": request.created_at.isoformat(),
                "expires_at": request.expires_at.isoformat(),
                "approvers": request.approvers,
                "metadata": request.metadata
            },
            ttl=int(self.approval_ttl.total_seconds())
        )
    
    async def _get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get approval request from cache."""
        key = f"approval:request:{request_id}"
        data = await self.cache.get(key)
        
        if not data:
            return None
            
        return ApprovalRequest(
            request_id=data["request_id"],
            requester_id=data["requester_id"],
            rollback_id=data["rollback_id"],
            validation_result=RollbackValidationResult(**data["validation_result"]),
            status=ApprovalStatus(data["status"]),
            required_level=ApprovalLevel(data["required_level"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            approvers=data["approvers"],
            metadata=data["metadata"]
        ) 