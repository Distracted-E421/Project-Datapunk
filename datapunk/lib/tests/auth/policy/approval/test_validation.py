import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from datapunk_shared.auth.policy.approval.validation import (
    ApprovalValidationConfig, ApprovalValidator
)
from datapunk_shared.auth.policy.approval.types import (
    ApprovalRequest, ApprovalLevel, ApprovalStatus
)
from datapunk_shared.auth.policy.types import PolicyType
from datapunk_shared.auth.policy.rollback.validation import (
    RollbackValidationResult, RollbackRisk
)
from datapunk_shared.core.exceptions import ValidationError

@pytest.fixture
def validation_config():
    """Create a sample validation configuration."""
    return ApprovalValidationConfig(
        max_approvers=5,
        require_different_approvers=True,
        allow_self_approval=False,
        expiry_hours=24,
        strict_mode=True,
        min_approval_level="team_lead"
    )

@pytest.fixture
def metrics_client():
    """Create a mock metrics client."""
    client = Mock()
    client.increment = Mock()
    return client

@pytest.fixture
def approval_validator(validation_config, metrics_client):
    """Create an ApprovalValidator instance with mock dependencies."""
    return ApprovalValidator(validation_config, metrics_client)

@pytest.fixture
def sample_request():
    """Create a sample approval request."""
    return ApprovalRequest(
        request_id="request-001",
        requester_id="user-001",
        policy_type=PolicyType.ACCESS,
        validation_result=RollbackValidationResult(
            is_valid=True,
            risk_level=RollbackRisk.MEDIUM,
            breaking_changes=[],
            warnings=[],
            recommendations=[]
        ),
        status=ApprovalStatus.PENDING,
        required_level=ApprovalLevel.TEAM_LEAD,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24),
        approvers=[],
        metadata={}
    )

@pytest.mark.asyncio
async def test_validate_request_success(approval_validator, sample_request):
    """Test successful request validation."""
    # Execute
    result = await approval_validator.validate_request(sample_request)
    
    # Verify
    assert result["valid"] is True
    assert len(result["issues"]) == 0
    approval_validator.metrics.increment.assert_called_once()

@pytest.mark.asyncio
async def test_validate_request_too_many_approvers(approval_validator, sample_request):
    """Test validation with too many approvers."""
    # Setup
    sample_request.approvers = ["user1", "user2", "user3", "user4", "user5", "user6"]
    
    # Execute
    result = await approval_validator.validate_request(sample_request)
    
    # Verify
    assert result["valid"] is False
    assert any("Too many approvers" in issue for issue in result["issues"])

@pytest.mark.asyncio
async def test_validate_request_self_approval(approval_validator, sample_request):
    """Test validation with self-approval attempt."""
    # Setup
    sample_request.approvers = [sample_request.requester_id]
    
    # Execute
    result = await approval_validator.validate_request(sample_request)
    
    # Verify
    assert result["valid"] is False
    assert any("Self-approval not allowed" in issue for issue in result["issues"])

@pytest.mark.asyncio
async def test_validate_request_duplicate_approvers(approval_validator, sample_request):
    """Test validation with duplicate approvers."""
    # Setup
    sample_request.approvers = ["user1", "user1", "user2"]
    
    # Execute
    result = await approval_validator.validate_request(sample_request)
    
    # Verify
    assert result["valid"] is False
    assert any("Duplicate approvers not allowed" in issue for issue in result["issues"])

@pytest.mark.asyncio
async def test_validate_request_low_approval_level(approval_validator, sample_request):
    """Test validation with low approval level."""
    # Setup
    sample_request.required_level = ApprovalLevel.TEAM_MEMBER
    
    # Execute
    result = await approval_validator.validate_request(sample_request)
    
    # Verify
    assert len(result["warnings"]) > 0
    assert any("Approval level below recommended minimum" in warning for warning in result["warnings"])

@pytest.mark.asyncio
async def test_validate_request_error_handling(approval_validator, sample_request):
    """Test error handling during request validation."""
    # Setup
    approval_validator.metrics.increment.side_effect = Exception("Metrics error")
    
    # Execute and verify
    with pytest.raises(ValidationError):
        await approval_validator.validate_request(sample_request)

@pytest.mark.asyncio
async def test_validate_approval_success(approval_validator, sample_request):
    """Test successful approval validation."""
    # Execute
    result = await approval_validator.validate_approval(
        request=sample_request,
        approver_id="approver-001",
        approver_level="team_lead"
    )
    
    # Verify
    assert result["valid"] is True
    assert len(result["issues"]) == 0

@pytest.mark.asyncio
async def test_validate_approval_non_pending_request(approval_validator, sample_request):
    """Test approval validation with non-pending request."""
    # Setup
    sample_request.status = ApprovalStatus.APPROVED
    
    # Execute
    result = await approval_validator.validate_approval(
        request=sample_request,
        approver_id="approver-001",
        approver_level="team_lead"
    )
    
    # Verify
    assert result["valid"] is False
    assert any("Request is not pending" in issue for issue in result["issues"])

@pytest.mark.asyncio
async def test_validate_approval_expired_request(approval_validator, sample_request):
    """Test approval validation with expired request."""
    # Setup
    sample_request.expires_at = datetime.utcnow() - timedelta(hours=1)
    
    # Execute
    result = await approval_validator.validate_approval(
        request=sample_request,
        approver_id="approver-001",
        approver_level="team_lead"
    )
    
    # Verify
    assert result["valid"] is False
    assert any("Request has expired" in issue for issue in result["issues"])

@pytest.mark.asyncio
async def test_validate_approval_insufficient_level(approval_validator, sample_request):
    """Test approval validation with insufficient authority level."""
    # Execute
    result = await approval_validator.validate_approval(
        request=sample_request,
        approver_id="approver-001",
        approver_level="team_member"  # Lower than required TEAM_LEAD
    )
    
    # Verify
    assert result["valid"] is False
    assert any("Insufficient approval level" in issue for issue in result["issues"])

@pytest.mark.asyncio
async def test_validate_approval_duplicate_approval(approval_validator, sample_request):
    """Test approval validation with duplicate approval attempt."""
    # Setup
    sample_request.approvers = ["approver-001"]
    
    # Execute
    result = await approval_validator.validate_approval(
        request=sample_request,
        approver_id="approver-001",
        approver_level="team_lead"
    )
    
    # Verify
    assert result["valid"] is False
    assert any("Approver has already approved" in issue for issue in result["issues"])

@pytest.mark.asyncio
async def test_validate_approval_error_handling(approval_validator, sample_request):
    """Test error handling during approval validation."""
    # Setup - create a condition that will raise an exception
    sample_request.status = None  # This will cause an error when comparing status
    
    # Execute and verify
    with pytest.raises(ValidationError):
        await approval_validator.validate_approval(
            request=sample_request,
            approver_id="approver-001",
            approver_level="team_lead"
        )

def test_validation_config_defaults():
    """Test validation configuration default values."""
    config = ApprovalValidationConfig()
    
    assert config.max_approvers == 5
    assert config.require_different_approvers is True
    assert config.allow_self_approval is False
    assert config.expiry_hours == 24
    assert config.strict_mode is True
    assert config.min_approval_level == "team_lead" 