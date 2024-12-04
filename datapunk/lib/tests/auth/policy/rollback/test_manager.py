import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from datapunk_shared.auth.policy.rollback.manager import (
    RollbackPoint, RollbackManager
)
from datapunk_shared.auth.policy.rollback.validation import (
    RollbackValidator, RollbackValidationResult, RollbackRisk
)
from datapunk_shared.auth.policy.types import PolicyType, PolicyStatus
from datapunk_shared.core.exceptions import AuthError

@pytest.fixture
def cache_client():
    """Create a mock cache client."""
    client = Mock()
    client.set = AsyncMock()
    client.get = AsyncMock()
    client.lpush = AsyncMock()
    client.lrange = AsyncMock()
    client.ltrim = AsyncMock()
    return client

@pytest.fixture
def metrics_client():
    """Create a mock metrics client."""
    client = Mock()
    client.increment = Mock()
    return client

@pytest.fixture
def validator():
    """Create a mock rollback validator."""
    validator = Mock()
    validator.validate_rollback = AsyncMock()
    return validator

@pytest.fixture
def rollback_manager(cache_client, metrics_client, validator):
    """Create a RollbackManager instance with mock dependencies."""
    return RollbackManager(
        cache_client=cache_client,
        metrics=metrics_client,
        validator=validator,
        max_history=10
    )

@pytest.fixture
def sample_policy():
    """Create a sample policy dictionary."""
    return {
        "type": "access",
        "rules": ["rule1", "rule2"],
        "version": "1.0.0"
    }

@pytest.fixture
def sample_rollback_point():
    """Create a sample rollback point."""
    return RollbackPoint(
        timestamp=datetime.utcnow(),
        policy_id="access_123456789",
        policy_type=PolicyType.ACCESS,
        old_policy={"type": "access", "rules": ["rule1"]},
        affected_keys=["key1", "key2"],
        metadata={"reason": "test rollback"}
    )

def test_rollback_point_creation():
    """Test RollbackPoint creation and properties."""
    now = datetime.utcnow()
    point = RollbackPoint(
        timestamp=now,
        policy_id="test_123",
        policy_type=PolicyType.ACCESS,
        old_policy={"test": "policy"},
        affected_keys=["key1"],
        metadata={"test": "metadata"}
    )
    
    assert point.timestamp == now
    assert point.policy_id == "test_123"
    assert point.policy_type == PolicyType.ACCESS
    assert point.old_policy == {"test": "policy"}
    assert point.affected_keys == ["key1"]
    assert point.metadata == {"test": "metadata"}

@pytest.mark.asyncio
async def test_create_rollback_point_success(rollback_manager, sample_policy):
    """Test successful creation of a rollback point."""
    # Execute
    policy_id = await rollback_manager.create_rollback_point(
        policy=sample_policy,
        policy_type=PolicyType.ACCESS,
        affected_keys=["key1", "key2"],
        metadata={"reason": "test"}
    )
    
    # Verify
    assert policy_id.startswith("access_")
    rollback_manager.cache.set.assert_called_once()
    rollback_manager.cache.lpush.assert_called_once()
    rollback_manager.metrics.increment.assert_called_once_with(
        "rollback_point_created",
        {"policy_type": PolicyType.ACCESS.value}
    )

@pytest.mark.asyncio
async def test_create_rollback_point_failure(rollback_manager, sample_policy):
    """Test rollback point creation failure."""
    # Setup
    rollback_manager.cache.set.side_effect = Exception("Cache error")
    
    # Execute and verify
    with pytest.raises(AuthError, match="Failed to create rollback point"):
        await rollback_manager.create_rollback_point(
            policy=sample_policy,
            policy_type=PolicyType.ACCESS,
            affected_keys=["key1"]
        )

@pytest.mark.asyncio
async def test_validate_rollback_success(rollback_manager, sample_rollback_point):
    """Test successful rollback validation."""
    # Setup
    rollback_manager.cache.get.side_effect = [
        {  # First call for rollback point
            "timestamp": sample_rollback_point.timestamp.isoformat(),
            "policy_type": sample_rollback_point.policy_type.value,
            "policy": sample_rollback_point.old_policy,
            "affected_keys": sample_rollback_point.affected_keys,
            "metadata": sample_rollback_point.metadata
        },
        {  # Second call for current policy
            "type": "access",
            "rules": ["rule1", "rule2"]
        }
    ]
    
    validation_result = RollbackValidationResult(
        is_valid=True,
        risk_level=RollbackRisk.LOW,
        breaking_changes=[],
        warnings=[],
        recommendations=[]
    )
    rollback_manager.validator.validate_rollback.return_value = validation_result
    
    # Execute
    result = await rollback_manager.validate_rollback(sample_rollback_point.policy_id)
    
    # Verify
    assert result.is_valid is True
    assert result.risk_level == RollbackRisk.LOW
    rollback_manager.validator.validate_rollback.assert_called_once()

@pytest.mark.asyncio
async def test_validate_rollback_point_not_found(rollback_manager):
    """Test validation with non-existent rollback point."""
    # Setup
    rollback_manager.cache.get.return_value = None
    
    # Execute and verify
    with pytest.raises(AuthError, match="Rollback point test_123 not found"):
        await rollback_manager.validate_rollback("test_123")

@pytest.mark.asyncio
async def test_validate_rollback_current_policy_not_found(rollback_manager, sample_rollback_point):
    """Test validation when current policy doesn't exist."""
    # Setup
    rollback_manager.cache.get.side_effect = [
        {  # First call for rollback point
            "timestamp": sample_rollback_point.timestamp.isoformat(),
            "policy_type": sample_rollback_point.policy_type.value,
            "policy": sample_rollback_point.old_policy,
            "affected_keys": sample_rollback_point.affected_keys,
            "metadata": sample_rollback_point.metadata
        },
        None  # Second call for current policy
    ]
    
    # Execute and verify
    with pytest.raises(AuthError, match="Current policy for access not found"):
        await rollback_manager.validate_rollback(sample_rollback_point.policy_id)

@pytest.mark.asyncio
async def test_cleanup_history(rollback_manager):
    """Test history cleanup when limit is exceeded."""
    # Setup
    history = [f"policy_{i}" for i in range(15)]  # More than max_history
    rollback_manager.cache.lrange.return_value = history
    
    # Execute
    await rollback_manager._cleanup_history(PolicyType.ACCESS.value)
    
    # Verify
    rollback_manager.cache.ltrim.assert_called_once()

@pytest.mark.asyncio
async def test_store_rollback_point(rollback_manager, sample_rollback_point):
    """Test storing a rollback point."""
    # Execute
    await rollback_manager._store_rollback_point(sample_rollback_point)
    
    # Verify
    rollback_manager.cache.set.assert_called_once()
    rollback_manager.cache.lpush.assert_called_once()
    
    # Verify stored data format
    stored_data = rollback_manager.cache.set.call_args[0][1]
    assert "timestamp" in stored_data
    assert "policy_type" in stored_data
    assert "policy" in stored_data
    assert "affected_keys" in stored_data
    assert "metadata" in stored_data 