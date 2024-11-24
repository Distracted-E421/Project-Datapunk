from typing import Dict, List, Optional, Set
import structlog
from dataclasses import dataclass
from datetime import datetime
from .policy_approval import ApprovalRequest, ApprovalLevel, ApprovalStatus
from .policy_notifications import NotificationManager

logger = structlog.get_logger()

@dataclass
class ApprovalStep:
    """Single step in approval chain."""
    level: ApprovalLevel
    required_approvers: int
    approvers: Set[str]
    approved_by: Set[str] = None
    approved_at: Optional[datetime] = None

class ApprovalChain:
    """Manages multi-level approval chains."""
    
    def __init__(self,
                 notification_manager: NotificationManager,
                 metrics_client):
        self.notifications = notification_manager
        self.metrics = metrics_client
        self.logger = logger.bind(component="approval_chain")
    
    async def create_chain(self,
                          request: ApprovalRequest,
                          steps: List[ApprovalStep]) -> str:
        """Create new approval chain."""
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
        """Process approval in chain."""
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
        """Store approval chain state."""
        await self.cache.set(
            f"approval_chain:{chain_id}",
            {
                "request": vars(request),
                "steps": [vars(step) for step in steps],
                "created_at": datetime.utcnow().isoformat()
            }
        )
    
    async def _get_chain(self, chain_id: str) -> Optional[Dict]:
        """Get approval chain state."""
        return await self.cache.get(f"approval_chain:{chain_id}")
    
    def _get_current_step(self, chain: Dict) -> Optional[ApprovalStep]:
        """Get current pending approval step."""
        for step in chain["steps"]:
            if not step.approved_at:
                return step
        return None
    
    def _get_next_step(self, chain: Dict) -> Optional[ApprovalStep]:
        """Get next approval step after current."""
        current = False
        for step in chain["steps"]:
            if current:
                return step
            if not step.approved_at:
                current = True
        return None
    
    async def _complete_chain(self, chain_id: str, chain: Dict) -> None:
        """Handle chain completion."""
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
        """Check if request requires urgent attention."""
        time_remaining = request.expires_at - datetime.utcnow()
        return time_remaining.total_seconds() < (
            self.notifications.config.urgent_threshold * 3600
        ) 