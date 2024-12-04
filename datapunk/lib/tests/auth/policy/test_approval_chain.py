import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from datapunk_shared.auth.policy.approval_chain import ApprovalChain, ApprovalStep
from datapunk_shared.auth.policy.policy_approval import ApprovalRequest, ApprovalLevel, ApprovalStatus
from datapunk_shared.auth.policy.types import PolicyValidationResult, RiskLevel

@pytest.fixture
def notification_manager():
    """Create a mock notification manager."""
    manager = Mock()
    manager.notify_approvers = AsyncMock()
    return manager

@pytest.fixture
def metrics_client():
    """Create a mock metrics client."""
    client = Mock()
    client.increment = Mock()
    return client

@pytest.fixture
def approval_chain(notification_manager, metrics_client):
    """Create an ApprovalChain instance with mock dependencies."""
    chain = ApprovalChain(notification_manager, metrics_client)
    chain.cache = AsyncMock()
    return chain

@pytest.fixture
def sample_approval_request():
    """Create a sample approval request."""
    return ApprovalRequest(
        request_id="test-request-001",
        policy_id="test-policy-001",
        requester_id="requester-001",
        validation_result=PolicyValidationResult(
            valid=True,
            issues=[],
            warnings=[],
            risk_level=RiskLevel.MEDIUM,
            breaking_changes=[]
        ),
        created_at=datetime.utcnow()
    )

@pytest.fixture
def sample_approval_steps():
    """Create a sample list of approval steps."""
    return [
        ApprovalStep(
            level=ApprovalLevel.TEAM_LEAD,
            required_approvers=1,
            approvers={"lead-001", "lead-002"},
            approved_by=set(),
        ),
        ApprovalStep(
            level=ApprovalLevel.SECURITY,
            required_approvers=2,
            approvers={"security-001", "security-002", "security-003"},
            approved_by=set(),
        )
    ]

@pytest.mark.asyncio
async def test_create_chain(approval_chain, sample_approval_request, sample_approval_steps):
    """Test creation of a new approval chain."""
    # Setup
    expected_chain_id = f"chain_{sample_approval_request.request_id}"
    
    # Execute
    chain_id = await approval_chain.create_chain(sample_approval_request, sample_approval_steps)
    
    # Verify
    assert chain_id == expected_chain_id
    approval_chain.cache.set.assert_called_once()
    approval_chain.notifications.notify_approvers.assert_called_once_with(
        sample_approval_request,
        is_urgent=False
    )
    approval_chain.metrics.increment.assert_called_once()

@pytest.mark.asyncio
async def test_process_approval_unauthorized(approval_chain, sample_approval_request, sample_approval_steps):
    """Test processing an approval from an unauthorized approver."""
    # Setup
    chain_id = "chain_001"
    approval_chain.cache.get.return_value = {
        "request": vars(sample_approval_request),
        "steps": [vars(step) for step in sample_approval_steps],
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Execute and verify
    with pytest.raises(ValueError, match="Unauthorized approver"):
        await approval_chain.process_approval(
            chain_id,
            "unauthorized-001",
            ApprovalLevel.TEAM_LEAD
        )

@pytest.mark.asyncio
async def test_process_approval_success(approval_chain, sample_approval_request, sample_approval_steps):
    """Test successful processing of an approval."""
    # Setup
    chain_id = "chain_001"
    approval_chain.cache.get.return_value = {
        "request": vars(sample_approval_request),
        "steps": [vars(step) for step in sample_approval_steps],
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Execute
    result = await approval_chain.process_approval(
        chain_id,
        "lead-001",
        ApprovalLevel.TEAM_LEAD
    )
    
    # Verify
    assert result is True
    approval_chain.cache.set.assert_called_once()
    approval_chain.notifications.notify_approvers.assert_called_once()

@pytest.mark.asyncio
async def test_process_approval_chain_completion(approval_chain, sample_approval_request, sample_approval_steps):
    """Test approval chain completion when all steps are approved."""
    # Setup
    chain_id = "chain_001"
    steps = sample_approval_steps.copy()
    # Mark first step as complete
    steps[0].approved_by = {"lead-001"}
    steps[0].approved_at = datetime.utcnow()
    # Second step needs one more approval
    steps[1].approved_by = {"security-001"}
    
    approval_chain.cache.get.return_value = {
        "request": vars(sample_approval_request),
        "steps": [vars(step) for step in steps],
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Execute
    result = await approval_chain.process_approval(
        chain_id,
        "security-002",
        ApprovalLevel.SECURITY
    )
    
    # Verify
    assert result is True
    # Verify chain completion
    assert len(steps[1].approved_by) >= steps[1].required_approvers

@pytest.mark.asyncio
async def test_process_approval_chain_not_found(approval_chain):
    """Test processing approval for non-existent chain."""
    # Setup
    approval_chain.cache.get.return_value = None
    
    # Execute and verify
    with pytest.raises(ValueError, match="Chain chain_001 not found"):
        await approval_chain.process_approval(
            "chain_001",
            "approver-001",
            ApprovalLevel.TEAM_LEAD
        )

def test_approval_step_creation():
    """Test creation of ApprovalStep."""
    step = ApprovalStep(
        level=ApprovalLevel.TEAM_LEAD,
        required_approvers=2,
        approvers={"lead-001", "lead-002", "lead-003"},
        approved_by=set(),
    )
    
    assert step.level == ApprovalLevel.TEAM_LEAD
    assert step.required_approvers == 2
    assert step.approvers == {"lead-001", "lead-002", "lead-003"}
    assert step.approved_by == set()
    assert step.approved_at is None 