import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from datapunk_shared.auth.policy.policy_migration import (
    MigrationStrategy, MigrationConfig, PolicyMigrator
)
from datapunk_shared.auth.api_keys.policies_extended import (
    AdvancedKeyPolicy, ResourceType, CompliancePolicy
)
from datapunk.lib.exceptions import MigrationError

@pytest.fixture
def cache_client():
    """Create a mock cache client."""
    client = Mock()
    client.set = AsyncMock()
    client.get = AsyncMock()
    client.delete = AsyncMock()
    return client

@pytest.fixture
def metrics_client():
    """Create a mock metrics client."""
    client = Mock()
    client.increment = Mock()
    return client

@pytest.fixture
def migration_config():
    """Create a sample migration configuration."""
    return MigrationConfig(
        strategy=MigrationStrategy.GRADUAL,
        grace_period_days=30,
        allow_rollback=True,
        validate_before_apply=True,
        notify_affected_users=True,
        backup_policies=True
    )

@pytest.fixture
def policy_migrator(cache_client, metrics_client, migration_config):
    """Create a PolicyMigrator instance with mock dependencies."""
    return PolicyMigrator(cache_client, metrics_client, migration_config)

@pytest.fixture
def old_policy():
    """Create a sample old policy."""
    return AdvancedKeyPolicy(
        type=ResourceType.API,
        allowed_resources={"resource1", "resource2"},
        rate_limit=100,
        compliance=CompliancePolicy(encryption_required=False)
    )

@pytest.fixture
def new_policy():
    """Create a sample new policy."""
    return AdvancedKeyPolicy(
        type=ResourceType.API,
        allowed_resources={"resource1", "resource2", "resource3"},
        rate_limit=150,
        compliance=CompliancePolicy(encryption_required=False)
    )

@pytest.fixture
def affected_keys():
    """Create a list of affected API keys."""
    return ["key1", "key2", "key3"]

def test_migration_strategy_enum():
    """Test MigrationStrategy enum values."""
    assert MigrationStrategy.IMMEDIATE.value == "immediate"
    assert MigrationStrategy.GRADUAL.value == "gradual"
    assert MigrationStrategy.PARALLEL.value == "parallel"

def test_migration_config_creation():
    """Test MigrationConfig creation and properties."""
    config = MigrationConfig(
        strategy=MigrationStrategy.GRADUAL,
        grace_period_days=15,
        allow_rollback=True,
        validate_before_apply=True,
        notify_affected_users=False,
        backup_policies=True
    )
    
    assert config.strategy == MigrationStrategy.GRADUAL
    assert config.grace_period_days == 15
    assert config.allow_rollback is True
    assert config.validate_before_apply is True
    assert config.notify_affected_users is False
    assert config.backup_policies is True

@pytest.mark.asyncio
async def test_migrate_policy_success(policy_migrator, old_policy, new_policy, affected_keys):
    """Test successful policy migration."""
    # Setup
    policy_migrator._validate_migration = AsyncMock()
    policy_migrator._backup_policy = AsyncMock()
    policy_migrator._gradual_migration = AsyncMock(return_value=True)
    policy_migrator._notify_users = AsyncMock()
    
    # Execute
    result = await policy_migrator.migrate_policy(old_policy, new_policy, affected_keys)
    
    # Verify
    assert result is True
    policy_migrator._validate_migration.assert_called_once()
    policy_migrator._backup_policy.assert_called_once()
    policy_migrator._gradual_migration.assert_called_once()
    policy_migrator._notify_users.assert_called_once()

@pytest.mark.asyncio
async def test_migrate_policy_validation_failure(policy_migrator, old_policy, new_policy, affected_keys):
    """Test migration failure due to validation."""
    # Setup
    policy_migrator._validate_migration.side_effect = MigrationError("Validation failed")
    
    # Execute and verify
    with pytest.raises(MigrationError, match="Validation failed"):
        await policy_migrator.migrate_policy(old_policy, new_policy, affected_keys)

@pytest.mark.asyncio
async def test_immediate_migration(policy_migrator, old_policy, new_policy, affected_keys):
    """Test immediate migration strategy."""
    # Setup
    policy_migrator.config.strategy = MigrationStrategy.IMMEDIATE
    
    # Execute
    result = await policy_migrator._immediate_migration(old_policy, new_policy, affected_keys)
    
    # Verify
    assert result is True
    assert policy_migrator.cache.set.call_count == len(affected_keys)
    assert policy_migrator.metrics.increment.call_count == len(affected_keys)

@pytest.mark.asyncio
async def test_gradual_migration(policy_migrator, old_policy, new_policy, affected_keys):
    """Test gradual migration strategy."""
    # Execute
    result = await policy_migrator._gradual_migration(old_policy, new_policy, affected_keys)
    
    # Verify
    assert result is True
    assert policy_migrator.cache.set.call_count == len(affected_keys)
    assert policy_migrator.metrics.increment.call_count == len(affected_keys)

@pytest.mark.asyncio
async def test_parallel_migration(policy_migrator, old_policy, new_policy, affected_keys):
    """Test parallel migration strategy."""
    # Execute
    result = await policy_migrator._parallel_migration(old_policy, new_policy, affected_keys)
    
    # Verify
    assert result is True
    assert policy_migrator.cache.set.call_count == len(affected_keys)
    assert policy_migrator.metrics.increment.call_count == len(affected_keys)

@pytest.mark.asyncio
async def test_validate_migration_breaking_changes(policy_migrator):
    """Test validation with breaking changes."""
    # Setup
    old = AdvancedKeyPolicy(
        type=ResourceType.API,
        allowed_resources={"resource1", "resource2"},
        rate_limit=100,
        compliance=CompliancePolicy(encryption_required=False)
    )
    new = AdvancedKeyPolicy(
        type=ResourceType.API,
        allowed_resources={"resource1"},  # Reduced resources
        rate_limit=50,  # Reduced rate limit
        compliance=CompliancePolicy(encryption_required=True)  # Added requirement
    )
    
    # Execute and verify
    with pytest.raises(MigrationError):
        policy_migrator.config.allow_rollback = False
        await policy_migrator._validate_migration(old, new)

@pytest.mark.asyncio
async def test_backup_policy(policy_migrator, old_policy):
    """Test policy backup creation."""
    # Execute
    await policy_migrator._backup_policy(old_policy)
    
    # Verify
    policy_migrator.cache.set.assert_called_once()
    assert "policy_backup:" in policy_migrator.cache.set.call_args[0][0] 