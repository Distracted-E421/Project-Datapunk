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
    """
    Manages the approval workflow for policy changes with configurable approval levels.
    
    This class handles the lifecycle of approval requests including creation, storage,
    validation, and status tracking. It integrates with caching and metrics systems
    for persistence and monitoring.
    
    Key responsibilities:
    - Determining appropriate approval levels based on risk assessment
    - Managing approval request lifecycle
    - Tracking request status and expiration
    - Monitoring approval metrics
    
    Dependencies:
    - CacheClient: For persistent storage of approval requests
    - MetricsClient: For tracking approval-related metrics
    """
    
    def __init__(self,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient',
                 approval_ttl: timedelta = timedelta(days=1)):
        """
        Initialize approval manager with required dependencies.
        
        Args:
            cache_client: Handles persistent storage of approval requests
            metrics: Tracks approval-related metrics
            approval_ttl: Time-to-live for approval requests (defaults to 24 hours)
        """
        self.cache = cache_client
        self.metrics = metrics
        self.approval_ttl = approval_ttl
        self.logger = logger.bind(component="approval_manager") 

    async def create_approval_request(self,
                                    requester_id: str,
                                    policy_type: PolicyType,
                                    validation_result: RollbackValidationResult,
                                    metadata: Optional[Dict] = None) -> ApprovalRequest:
        """
        Create and store a new approval request with appropriate validation.
        
        The approval level is determined based on the risk level and presence of
        breaking changes in the validation result. Requests are validated before
        storage and metrics are recorded for monitoring.
        
        Args:
            requester_id: Unique identifier of the requesting user/system
            policy_type: Type of policy being modified
            validation_result: Results from rollback validation including risk assessment
            metadata: Optional additional context for the request
            
        Returns:
            ApprovalRequest: The created and stored approval request
            
        Raises:
            ApprovalError: If request creation or validation fails
        
        NOTE: Request IDs are generated using UTC timestamp to ensure uniqueness
        """
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
        """
        Retrieve all pending approval requests, optionally filtered by policy type.
        
        Uses cache scanning to find all approval requests and filters for pending
        status. Performance may degrade with large numbers of requests.
        
        Args:
            policy_type: Optional filter to return only requests for specific policy type
            
        Returns:
            List[ApprovalRequest]: List of pending approval requests
            
        Raises:
            ApprovalError: If request fetching fails
            
        TODO: Consider implementing pagination for large result sets
        """
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
        """
        Check the current status of an approval request.
        
        Provides detailed status information including approvers and expiration.
        The metadata field can be used to track custom workflow states.
        
        Args:
            request_id: Unique identifier of the approval request
            
        Returns:
            Dict containing status details:
            - status: Current approval status
            - approvers: List of users who have approved
            - expires_at: ISO formatted expiration timestamp
            - metadata: Custom workflow metadata
            
        Raises:
            ApprovalError: If request is not found or status check fails
        """
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