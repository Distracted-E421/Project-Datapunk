import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from datapunk_shared.auth.policy.delegation_audit import (
    DelegationAction, DelegationAuditEvent, DelegationAuditor
)
from datapunk_shared.auth.policy.approval_delegation import DelegationType, DelegationRule
from datapunk_shared.auth.policy.policy_approval import ApprovalLevel

@pytest.fixture
def audit_logger():
    """Create a mock audit logger."""
    logger = Mock()
    logger.log_event = AsyncMock()
    return logger

@pytest.fixture
def metrics_client():
    """Create a mock metrics client."""
    client = Mock()
    client.increment = Mock()
    return client

@pytest.fixture
def delegation_auditor(audit_logger, metrics_client):
    """Create a DelegationAuditor instance with mock dependencies."""
    return DelegationAuditor(audit_logger, metrics_client)

@pytest.fixture
def sample_audit_event():
    """Create a sample delegation audit event."""
    return DelegationAuditEvent(
        timestamp=datetime.utcnow(),
        action=DelegationAction.CREATE,
        delegator_id="delegator-001",
        delegate_id="delegate-001",
        delegation_type=DelegationType.TEMPORARY,
        level=ApprovalLevel.TEAM_LEAD.value,
        success=True,
        reason="Test delegation",
        metadata={"test": "metadata"},
        ip_address="127.0.0.1",
        session_id="session-001"
    )

@pytest.fixture
def sample_delegation_rule():
    """Create a sample delegation rule."""
    return DelegationRule(
        delegator_id="delegator-001",
        delegate_id="delegate-001",
        level=ApprovalLevel.TEAM_LEAD,
        type=DelegationType.TEMPORARY,
        conditions={"business_hours": True},
        expires_at=datetime.utcnow()
    )

def test_delegation_action_enum():
    """Test DelegationAction enum values."""
    assert DelegationAction.CREATE.value == "create"
    assert DelegationAction.REVOKE.value == "revoke"
    assert DelegationAction.USE.value == "use"
    assert DelegationAction.EXPIRE.value == "expire"
    assert DelegationAction.MODIFY.value == "modify"
    assert DelegationAction.VALIDATE.value == "validate"

def test_delegation_audit_event_creation():
    """Test DelegationAuditEvent creation and properties."""
    now = datetime.utcnow()
    event = DelegationAuditEvent(
        timestamp=now,
        action=DelegationAction.CREATE,
        delegator_id="delegator-001",
        delegate_id="delegate-001",
        delegation_type=DelegationType.TEMPORARY,
        level=ApprovalLevel.TEAM_LEAD.value,
        success=True,
        reason="Test event",
        metadata={"test": "data"},
        ip_address="127.0.0.1",
        session_id="session-001"
    )
    
    assert event.timestamp == now
    assert event.action == DelegationAction.CREATE
    assert event.delegator_id == "delegator-001"
    assert event.delegate_id == "delegate-001"
    assert event.delegation_type == DelegationType.TEMPORARY
    assert event.level == ApprovalLevel.TEAM_LEAD.value
    assert event.success is True
    assert event.reason == "Test event"
    assert event.metadata == {"test": "data"}
    assert event.ip_address == "127.0.0.1"
    assert event.session_id == "session-001"

@pytest.mark.asyncio
async def test_log_delegation_event_success(delegation_auditor, sample_audit_event):
    """Test successful logging of a delegation event."""
    # Execute
    result = await delegation_auditor.log_delegation_event(sample_audit_event)
    
    # Verify
    assert result is True
    delegation_auditor.audit.log_event.assert_called_once()
    delegation_auditor.metrics.increment.assert_called_once_with(
        "delegation_operations_total",
        {
            "action": sample_audit_event.action.value,
            "type": sample_audit_event.delegation_type.value,
            "success": "true"
        }
    )

@pytest.mark.asyncio
async def test_log_delegation_event_failure(delegation_auditor, sample_audit_event):
    """Test handling of logging failure."""
    # Setup
    delegation_auditor.audit.log_event.side_effect = Exception("Logging error")
    
    # Execute
    result = await delegation_auditor.log_delegation_event(sample_audit_event)
    
    # Verify
    assert result is False

@pytest.mark.asyncio
async def test_log_creation(delegation_auditor, sample_delegation_rule):
    """Test logging of delegation creation."""
    # Execute
    await delegation_auditor.log_creation(
        rule=sample_delegation_rule,
        success=True,
        reason="Test creation",
        metadata={"test": "metadata"},
        ip_address="127.0.0.1",
        session_id="session-001"
    )
    
    # Verify
    delegation_auditor.audit.log_event.assert_called_once()
    args = delegation_auditor.audit.log_event.call_args[0]
    assert args[0] == "delegation_audit"
    assert args[1]["action"] == DelegationAction.CREATE.value
    assert args[1]["success"] is True

@pytest.mark.asyncio
async def test_log_revocation(delegation_auditor):
    """Test logging of delegation revocation."""
    # Execute
    await delegation_auditor.log_revocation(
        delegator_id="delegator-001",
        delegate_id="delegate-001",
        success=True,
        reason="Test revocation",
        metadata={"test": "metadata"},
        ip_address="127.0.0.1",
        session_id="session-001"
    )
    
    # Verify
    delegation_auditor.audit.log_event.assert_called_once()
    args = delegation_auditor.audit.log_event.call_args[0]
    assert args[0] == "delegation_audit"
    assert args[1]["action"] == DelegationAction.REVOKE.value
    assert args[1]["success"] is True

@pytest.mark.asyncio
async def test_log_usage(delegation_auditor):
    """Test logging of delegation usage."""
    # Execute
    await delegation_auditor.log_usage(
        delegator_id="delegator-001",
        delegate_id="delegate-001",
        level=ApprovalLevel.TEAM_LEAD.value,
        success=True,
        reason="Test usage",
        metadata={"test": "metadata"},
        ip_address="127.0.0.1",
        session_id="session-001"
    )
    
    # Verify
    delegation_auditor.audit.log_event.assert_called_once()
    args = delegation_auditor.audit.log_event.call_args[0]
    assert args[0] == "delegation_audit"
    assert args[1]["action"] == DelegationAction.USE.value
    assert args[1]["success"] is True 