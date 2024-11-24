from typing import Dict, List, Optional, TYPE_CHECKING, Any
from datetime import datetime, timedelta
import structlog
from enum import Enum
from dataclasses import dataclass

from ..rollback.validation import RollbackValidationResult, RollbackRisk
from .types import ApprovalStatus, ApprovalLevel, ApprovalRequest
from ....exceptions import ApprovalError

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....cache import CacheClient

logger = structlog.get_logger()

class ApprovalManager:
    """Manages approval workflow for policy changes."""
    
    def __init__(self,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient',
                 approval_ttl: timedelta = timedelta(days=1)):
        self.cache = cache_client
        self.metrics = metrics
        self.approval_ttl = approval_ttl
        self.logger = logger.bind(component="approval_manager") 

    async def create_approval_request(self,
                                    requester_id: str,
                                    policy_type: PolicyType,
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
                policy_type=policy_type,
                validation_result=validation_result,
                status=ApprovalStatus.PENDING,
                required_level=required_level,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + self.approval_ttl,
                approvers=[],
                metadata=metadata
            )
            
            # Validate request
            validation_result = await self.validator.validate_request(request)
            if not validation_result["valid"]:
                raise ApprovalError(
                    f"Invalid approval request: {validation_result['issues']}"
                )
            
            # Store request
            await self._store_request(request)
            
            # Update metrics
            self.metrics.increment(
                "approval_requests_created",
                {
                    "risk_level": validation_result.risk_level.value,
                    "approval_level": required_level.value,
                    "policy_type": policy_type.value
                }
            )
            
            return request
            
        except Exception as e:
            self.logger.error("approval_request_creation_failed",
                            error=str(e))
            raise ApprovalError(f"Failed to create approval request: {str(e)}")
    
    async def get_pending_requests(self,
                                 policy_type: Optional[PolicyType] = None) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        try:
            pattern = f"approval:request:*"
            keys = await self.cache.scan(pattern)
            
            requests = []
            for key in keys:
                request = await self._get_request(key.split(":")[-1])
                if request and request.status == ApprovalStatus.PENDING:
                    if not policy_type or request.policy_type == policy_type:
                        requests.append(request)
            
            return requests
            
        except Exception as e:
            self.logger.error("pending_requests_fetch_failed",
                            error=str(e))
            raise ApprovalError(f"Failed to fetch pending requests: {str(e)}")
    
    async def check_request_status(self,
                                 request_id: str) -> Dict[str, Any]:
        """Check status of an approval request."""
        try:
            request = await self._get_request(request_id)
            if not request:
                raise ApprovalError(f"Request {request_id} not found")
            
            return {
                "status": request.status.value,
                "approvers": request.approvers,
                "expires_at": request.expires_at.isoformat(),
                "metadata": request.metadata
            }
            
        except Exception as e:
            self.logger.error("status_check_failed",
                            request_id=request_id,
                            error=str(e))
            raise