import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
from datapunk_shared.auth.policy.approval_delegation import (
    DelegationType, DelegationRule, DelegationManager
)
from datapunk_shared.auth.policy.policy_approval import ApprovalLevel
from datapunk_shared.exceptions import DelegationError

@pytest.fixture
def cache_client():
    """Create a mock cache client."""
    client = Mock()
    client.set = AsyncMock()
    client.get = AsyncMock()
    client.delete = AsyncMock()
    client.keys = AsyncMock()
    return client

@pytest.fixture
def metrics_client():
    """Create a mock metrics client."""
    client = Mock()
    client.increment = Mock()
    return client

@pytest.fixture
def delegation_manager(cache_client, metrics_client):
    """Create a DelegationManager instance with mock dependencies."""
    return DelegationManager(cache_client, metrics_client)

@pytest.fixture
def sample_delegation_rule():
    """Create a sample delegation rule."""
    return DelegationRule(
        delegator_id="delegator-001",
        delegate_id="delegate-001",
        level=ApprovalLevel.TEAM_LEAD,
        type=DelegationType.TEMPORARY,
        conditions={"business_hours": True},
        expires_at=datetime.utcnow() + timedelta(days=7)
    )

@pytest.mark.asyncio
async def test_create_delegation_success(delegation_manager, sample_delegation_rule):
    """Test successful creation of a delegation."""
    # Setup
    delegation_manager._validate_delegation = AsyncMock()
    
    # Execute
    result = await delegation_manager.create_delegation(sample_delegation_rule)
    
    # Verify
    assert result is True
    delegation_manager.cache.set.assert_called_once()
    delegation_manager.metrics.increment.assert_called_once_with(
        "delegations_created",
        {"type": sample_delegation_rule.type.value}
    )

@pytest.mark.asyncio
async def test_create_delegation_failure(delegation_manager, sample_delegation_rule):
    """Test delegation creation failure."""
    # Setup
    delegation_manager.cache.set.side_effect = Exception("Cache error")
    
    # Execute and verify
    with pytest.raises(DelegationError, match="Failed to create delegation"):
        await delegation_manager.create_delegation(sample_delegation_rule)

@pytest.mark.asyncio
async def test_check_delegation_valid(delegation_manager, sample_delegation_rule):
    """Test checking a valid delegation."""
    # Setup
    delegation_manager.cache.get.return_value = {
        "level": sample_delegation_rule.level.value,
        "type": sample_delegation_rule.type.value,
        "conditions": sample_delegation_rule.conditions,
        "expires_at": sample_delegation_rule.expires_at.isoformat(),
        "created_at": sample_delegation_rule.created_at.isoformat()
    }
    
    # Execute
    result = await delegation_manager.check_delegation(
        sample_delegation_rule.delegator_id,
        sample_delegation_rule.delegate_id,
        sample_delegation_rule.level
    )
    
    # Verify
    assert result is True

@pytest.mark.asyncio
async def test_check_delegation_expired(delegation_manager, sample_delegation_rule):
    """Test checking an expired delegation."""
    # Setup
    expired_time = datetime.utcnow() - timedelta(days=1)
    delegation_manager.cache.get.return_value = {
        "level": sample_delegation_rule.level.value,
        "type": sample_delegation_rule.type.value,
        "conditions": sample_delegation_rule.conditions,
        "expires_at": expired_time.isoformat(),
        "created_at": sample_delegation_rule.created_at.isoformat()
    }
    
    # Execute
    result = await delegation_manager.check_delegation(
        sample_delegation_rule.delegator_id,
        sample_delegation_rule.delegate_id,
        sample_delegation_rule.level
    )
    
    # Verify
    assert result is False
    delegation_manager.cache.delete.assert_called_once()

@pytest.mark.asyncio
async def test_check_delegation_insufficient_level(delegation_manager, sample_delegation_rule):
    """Test checking a delegation with insufficient authority level."""
    # Setup
    delegation_manager.cache.get.return_value = {
        "level": ApprovalLevel.TEAM_LEAD.value,
        "type": sample_delegation_rule.type.value,
        "conditions": sample_delegation_rule.conditions,
        "expires_at": sample_delegation_rule.expires_at.isoformat(),
        "created_at": sample_delegation_rule.created_at.isoformat()
    }
    
    # Execute
    result = await delegation_manager.check_delegation(
        sample_delegation_rule.delegator_id,
        sample_delegation_rule.delegate_id,
        ApprovalLevel.SECURITY  # Higher level than TEAM_LEAD
    )
    
    # Verify
    assert result is False

@pytest.mark.asyncio
async def test_revoke_delegation_success(delegation_manager, sample_delegation_rule):
    """Test successful delegation revocation."""
    # Execute
    result = await delegation_manager.revoke_delegation(
        sample_delegation_rule.delegator_id,
        sample_delegation_rule.delegate_id
    )
    
    # Verify
    assert result is True
    delegation_manager.cache.delete.assert_called_once()
    delegation_manager.metrics.increment.assert_called_once_with("delegations_revoked")

@pytest.mark.asyncio
async def test_get_delegations_success(delegation_manager, sample_delegation_rule):
    """Test successful retrieval of delegations."""
    # Setup
    key = f"delegation:{sample_delegation_rule.delegator_id}:{sample_delegation_rule.delegate_id}"
    delegation_manager.cache.keys.return_value = [key]
    delegation_manager.cache.get.return_value = {
        "level": sample_delegation_rule.level.value,
        "type": sample_delegation_rule.type.value,
        "conditions": sample_delegation_rule.conditions,
        "expires_at": sample_delegation_rule.expires_at.isoformat(),
        "created_at": sample_delegation_rule.created_at.isoformat()
    }
    
    # Execute
    delegations = await delegation_manager.get_delegations(sample_delegation_rule.delegator_id)
    
    # Verify
    assert len(delegations) == 1
    delegation = delegations[0]
    assert delegation.delegator_id == sample_delegation_rule.delegator_id
    assert delegation.delegate_id == sample_delegation_rule.delegate_id
    assert delegation.level == sample_delegation_rule.level
    assert delegation.type == sample_delegation_rule.type

def test_delegation_type_enum():
    """Test DelegationType enum values."""
    assert DelegationType.TEMPORARY.value == "temporary"
    assert DelegationType.PERMANENT.value == "permanent"
    assert DelegationType.CONDITIONAL.value == "conditional"

def test_delegation_rule_creation():
    """Test DelegationRule creation and properties."""
    now = datetime.utcnow()
    expires = now + timedelta(days=7)
    
    rule = DelegationRule(
        delegator_id="delegator-001",
        delegate_id="delegate-001",
        level=ApprovalLevel.TEAM_LEAD,
        type=DelegationType.TEMPORARY,
        conditions={"business_hours": True},
        expires_at=expires,
        created_at=now
    )
    
    assert rule.delegator_id == "delegator-001"
    assert rule.delegate_id == "delegate-001"
    assert rule.level == ApprovalLevel.TEAM_LEAD
    assert rule.type == DelegationType.TEMPORARY
    assert rule.conditions == {"business_hours": True}
    assert rule.expires_at == expires
    assert rule.created_at == now 