import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
from datapunk_shared.auth.policy.approval.manager import ApprovalManager
from datapunk_shared.auth.policy.approval.types import (
    ApprovalStatus, ApprovalLevel, ApprovalRequest
)
from datapunk_shared.auth.policy.types import PolicyType
from datapunk_shared.auth.policy.rollback.validation import (
    RollbackValidationResult, RollbackRisk
)
from datapunk.lib.exceptions import ApprovalError

@pytest.fixture
def cache_client():
    """Create a mock cache client."""
    client = Mock()
    client.set = AsyncMock()
    client.get = AsyncMock()
    client.scan = AsyncMock()
    return client

@pytest.fixture
def metrics_client():
    """Create a mock metrics client."""
    client = Mock()
    client.increment = Mock()
    return client

@pytest.fixture
def approval_manager(cache_client, metrics_client):
    """Create an ApprovalManager instance with mock dependencies."""
    manager = ApprovalManager(
        cache_client=cache_client,
        metrics=metrics_client,
        approval_ttl=timedelta(days=1)
    )
    manager.validator = Mock()
    manager.validator.validate_request = AsyncMock(return_value={"valid": True})
    return manager

@pytest.fixture
def validation_result():
    """Create a sample validation result."""
    return RollbackValidationResult(
        is_valid=True,
        risk_level=RollbackRisk.MEDIUM,
        breaking_changes=[],
        warnings=["Test warning"],
        recommendations=["Test recommendation"]
    )

@pytest.fixture
def sample_request():
    """Create a sample approval request."""
    return ApprovalRequest(
        request_id="apr_123456789",
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
        expires_at=datetime.utcnow() + timedelta(days=1),
        approvers=[],
        metadata={"test": "metadata"}
    )

@pytest.mark.asyncio
async def test_create_approval_request_success(approval_manager, validation_result):
    """Test successful creation of an approval request."""
    # Execute
    request = await approval_manager.create_approval_request(
        requester_id="user-001",
        policy_type=PolicyType.ACCESS,
        validation_result=validation_result,
        metadata={"test": "metadata"}
    )
    
    # Verify
    assert isinstance(request, ApprovalRequest)
    assert request.requester_id == "user-001"
    assert request.policy_type == PolicyType.ACCESS
    assert request.status == ApprovalStatus.PENDING
    approval_manager.cache.set.assert_called_once()
    approval_manager.metrics.increment.assert_called_once()

@pytest.mark.asyncio
async def test_create_approval_request_validation_failure(approval_manager, validation_result):
    """Test approval request creation with validation failure."""
    # Setup
    approval_manager.validator.validate_request.return_value = {
        "valid": False,
        "issues": ["Test validation error"]
    }
    
    # Execute and verify
    with pytest.raises(ApprovalError, match="Invalid approval request"):
        await approval_manager.create_approval_request(
            requester_id="user-001",
            policy_type=PolicyType.ACCESS,
            validation_result=validation_result
        )

@pytest.mark.asyncio
async def test_get_pending_requests_success(approval_manager, sample_request):
    """Test successful retrieval of pending requests."""
    # Setup
    approval_manager.cache.scan.return_value = ["approval:request:123"]
    approval_manager.cache.get.return_value = vars(sample_request)
    
    # Execute
    requests = await approval_manager.get_pending_requests()
    
    # Verify
    assert len(requests) == 1
    assert isinstance(requests[0], ApprovalRequest)
    assert requests[0].status == ApprovalStatus.PENDING

@pytest.mark.asyncio
async def test_get_pending_requests_filtered(approval_manager, sample_request):
    """Test retrieval of pending requests filtered by policy type."""
    # Setup
    approval_manager.cache.scan.return_value = ["approval:request:123"]
    approval_manager.cache.get.return_value = vars(sample_request)
    
    # Execute
    requests = await approval_manager.get_pending_requests(PolicyType.ACCESS)
    
    # Verify
    assert len(requests) == 1
    assert requests[0].policy_type == PolicyType.ACCESS

@pytest.mark.asyncio
async def test_get_pending_requests_empty(approval_manager):
    """Test retrieval of pending requests when none exist."""
    # Setup
    approval_manager.cache.scan.return_value = []
    
    # Execute
    requests = await approval_manager.get_pending_requests()
    
    # Verify
    assert len(requests) == 0

@pytest.mark.asyncio
async def test_check_request_status_success(approval_manager, sample_request):
    """Test successful request status check."""
    # Setup
    approval_manager.cache.get.return_value = vars(sample_request)
    
    # Execute
    status = await approval_manager.check_request_status(sample_request.request_id)
    
    # Verify
    assert status["status"] == ApprovalStatus.PENDING.value
    assert status["approvers"] == []
    assert "expires_at" in status
    assert status["metadata"] == {"test": "metadata"}

@pytest.mark.asyncio
async def test_check_request_status_not_found(approval_manager):
    """Test status check for non-existent request."""
    # Setup
    approval_manager.cache.get.return_value = None
    
    # Execute and verify
    with pytest.raises(ApprovalError, match="Request test-123 not found"):
        await approval_manager.check_request_status("test-123")

@pytest.mark.asyncio
async def test_check_request_status_error(approval_manager):
    """Test error handling in status check."""
    # Setup
    approval_manager.cache.get.side_effect = Exception("Cache error")
    
    # Execute and verify
    with pytest.raises(ApprovalError):
        await approval_manager.check_request_status("test-123")

def test_approval_ttl_configuration():
    """Test custom TTL configuration."""
    custom_ttl = timedelta(hours=12)
    manager = ApprovalManager(
        cache_client=Mock(),
        metrics=Mock(),
        approval_ttl=custom_ttl
    )
    assert manager.approval_ttl == custom_ttl 