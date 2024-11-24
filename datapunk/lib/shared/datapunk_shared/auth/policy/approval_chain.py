from typing import Dict, List, Optional, Set
import structlog
from dataclasses import dataclass
from datetime import datetime
from .policy_approval import ApprovalRequest, ApprovalLevel, ApprovalStatus
from .policy_notifications import NotificationManager

logger = structlog.get_logger()

@dataclass
class ApprovalStep:
    """
    Represents a single step in an approval chain workflow.
    
    Each step requires a specific number of approvers from an authorized set
    to approve before proceeding to the next step. This enables hierarchical
    or parallel approval processes.
    """
    level: ApprovalLevel  # Hierarchical level in approval chain
    required_approvers: int  # Minimum approvals needed to complete step
    approvers: Set[str]  # Set of authorized approver IDs for this step
    approved_by: Set[str] = None  # Tracks who has approved
    approved_at: Optional[datetime] = None  # Timestamp of step completion

class ApprovalChain:
    """
    Manages multi-level approval chain workflows with configurable steps and notifications.
    
    This class orchestrates the entire approval process, including:
    - Creating and storing approval chains
    - Processing approvals and managing state transitions
    - Handling notifications at each step
    - Tracking metrics for monitoring and compliance
    
    The approval chain supports both sequential and parallel approval patterns,
    with built-in urgency handling based on expiration times.
    """
    
    def __init__(self,
                 notification_manager: NotificationManager,
                 metrics_client):
        """
        Initialize approval chain manager with required dependencies.
        
        NOTE: Requires a configured cache backend for state persistence
        TODO: Consider adding retry logic for notification delivery
        """
        self.notifications = notification_manager
        self.metrics = metrics_client
        self.logger = logger.bind(component="approval_chain")
    
    async def create_chain(self,
                          request: ApprovalRequest,
                          steps: List[ApprovalStep]) -> str:
        """
        Create new approval chain with specified steps.
        
        Chain ID format: chain_<request_id> ensures traceability back to original request.
        Notifies initial approvers and tracks creation in metrics for monitoring.
        
        IMPORTANT: Assumes steps are ordered by approval level
        """
        try:
            chain_id = f"chain_{request.request_id}"
            
            # Store chain configuration
            await self._store_chain(chain_id, request, steps)
            
            # Notify first level approvers
            await self.notifications.notify_approvers(
                request,
                is_urgent=self._is_urgent(request)
            )
            
            # Update metrics
            self.metrics.increment(
                "approval_chains_created",
                {"risk_level": request.validation_result.risk_level.value}
            )
            
            return chain_id
            
        except Exception as e:
            self.logger.error("chain_creation_failed",
                            error=str(e))
            raise
    
    async def process_approval(self,
                             chain_id: str,
                             approver_id: str,
                             approver_level: ApprovalLevel,
                             comments: Optional[str] = None) -> bool:
        """
        Process an approval action within the chain.
        
        Validates approver authorization and manages transition to next step
        when required approvals are met. Handles chain completion when all
        steps are approved.
        
        FIXME: Add support for approval rejection and rollback
        TODO: Implement comment persistence and audit trail
        """
        try:
            chain = await self._get_chain(chain_id)
            if not chain:
                raise ValueError(f"Chain {chain_id} not found")
            
            current_step = self._get_current_step(chain)
            if not current_step:
                raise ValueError("No pending approval steps")
            
            # Validate approver
            if approver_id not in current_step.approvers:
                raise ValueError("Unauthorized approver")
            
            # Record approval
            current_step.approved_by.add(approver_id)
            current_step.approved_at = datetime.utcnow()
            
            # Check if step is complete
            if len(current_step.approved_by) >= current_step.required_approvers:
                # Move to next step
                next_step = self._get_next_step(chain)
                if next_step:
                    await self.notifications.notify_approvers(
                        chain["request"],
                        is_urgent=self._is_urgent(chain["request"])
                    )
                else:
                    # Chain complete
                    await self._complete_chain(chain_id, chain)
            
            # Update chain state
            await self._store_chain(chain_id, chain["request"], chain["steps"])
            
            return True
            
        except Exception as e:
            self.logger.error("approval_processing_failed",
                            chain_id=chain_id,
                            error=str(e))
            raise
    
    async def _store_chain(self,
                          chain_id: str,
                          request: ApprovalRequest,
                          steps: List[ApprovalStep]) -> None:
        """
        Persist approval chain state to cache.
        
        NOTE: Cache TTL should align with request expiration to prevent
        orphaned chain data. Current implementation uses request vars()
        which may need revision if request model changes.
        """
        await self.cache.set(
            f"approval_chain:{chain_id}",
            {
                "request": vars(request),
                "steps": [vars(step) for step in steps],
                "created_at": datetime.utcnow().isoformat()
            }
        )
    
    async def _get_chain(self, chain_id: str) -> Optional[Dict]:
        """
        Retrieve approval chain state from cache.
        
        Args:
            chain_id: Unique identifier for the approval chain
            
        Returns:
            Dict containing chain state or None if not found
            
        NOTE: Cache misses should be treated as chain expiration/deletion
        rather than errors, as chains may be legitimately removed after
        completion or timeout
        """
        return await self.cache.get(f"approval_chain:{chain_id}")
    
    def _get_current_step(self, chain: Dict) -> Optional[ApprovalStep]:
        """
        Identify the current pending approval step in the chain.
        
        Finds first unapproved step in the sequence. This implementation
        assumes steps are processed strictly in order and cannot be skipped.
        
        Args:
            chain: Dictionary containing full chain state
            
        Returns:
            First ApprovalStep without approval timestamp, or None if chain complete
            
        NOTE: Returns None for completed chains, which should trigger chain
        completion logic in the caller
        """
        for step in chain["steps"]:
            if not step.approved_at:
                return step
        return None
    
    def _get_next_step(self, chain: Dict) -> Optional[ApprovalStep]:
        """
        Determine the next step that will become active after current approval.
        
        Used for preparing notifications and validating chain progression.
        Implementation maintains sequential order of approvals while supporting
        parallel approvers within each step.
        
        Args:
            chain: Dictionary containing full chain state
            
        Returns:
            Next ApprovalStep in sequence or None if at final step
            
        NOTE: The 'current' flag tracks position relative to first unapproved
        step, ensuring we return the next sequential step even if previous
        steps have multiple approvers
        """
        current = False
        for step in chain["steps"]:
            if current:
                return step
            if not step.approved_at:
                current = True
        return None
    
    async def _complete_chain(self, chain_id: str, chain: Dict) -> None:
        """
        Finalize approval chain after all steps are approved.
        
        Performs necessary cleanup and notifications:
        1. Updates request status to APPROVED
        2. Notifies original requestor of completion
        3. Records completion metrics for monitoring
        
        Args:
            chain_id: Unique identifier for the approval chain
            chain: Dictionary containing full chain state
            
        NOTE: This method should only be called after validating that all
        steps are complete to maintain data consistency
        
        TODO: Consider adding chain archival logic for audit purposes
        FIXME: Add handling for chain completion notification failures
        """
        request = chain["request"]
        
        # Update request status
        request.status = ApprovalStatus.APPROVED
        
        # Notify requestor
        await self.notifications.notify_requestor(
            request,
            ApprovalStatus.APPROVED
        )
        
        # Update metrics
        self.metrics.increment(
            "approval_chains_completed",
            {"risk_level": request.validation_result.risk_level.value}
        )
    
    def _is_urgent(self, request: ApprovalRequest) -> bool:
        """
        Determine if request needs urgent handling based on time remaining.
        
        Urgency threshold is configured in notification manager and converted
        to seconds for comparison. This affects notification priority and
        delivery methods.
        
        NOTE: Time calculations assume UTC timestamps throughout
        """
        time_remaining = request.expires_at - datetime.utcnow()
        return time_remaining.total_seconds() < (
            self.notifications.config.urgent_threshold * 3600
        ) 