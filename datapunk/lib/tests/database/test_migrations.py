import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from pathlib import Path
from datapunk_shared.database.migrations import (
    MigrationState,
    MigrationConfig,
    MigrationManager,
    MigrationError
)
from datapunk_shared.monitoring import MetricsCollector

@pytest.fixture
def migration_config():
    return MigrationConfig(
        batch_size=10,
        timeout_seconds=30,
        parallel_migrations=2
    )

@pytest.fixture
def metrics_collector():
    return Mock(spec=MetricsCollector)

@pytest.fixture
async def migration_manager(migration_config, metrics_collector):
    manager = MigrationManager(
        config=migration_config,
        metrics_collector=metrics_collector,
        dsn="postgresql://test:test@localhost:5432/test_db"
    )
    yield manager
    await manager.cleanup()

@pytest.fixture
def sample_migration():
    return {
        "version": "1.0.0",
        "name": "create_users_table",
        "up": "CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT);",
        "down": "DROP TABLE users;",
        "checksum": "abc123"
    }

@pytest.mark.asyncio
async def test_migration_state_transitions(migration_manager):
    migration_id = "test_migration"
    
    # Test state transitions
    await migration_manager.set_migration_state(migration_id, MigrationState.PENDING)
    state = await migration_manager.get_migration_state(migration_id)
    assert state == MigrationState.PENDING
    
    await migration_manager.set_migration_state(migration_id, MigrationState.IN_PROGRESS)
    state = await migration_manager.get_migration_state(migration_id)
    assert state == MigrationState.IN_PROGRESS

@pytest.mark.asyncio
async def test_migration_execution(migration_manager, sample_migration):
    with patch.object(migration_manager, '_execute_migration') as mock_execute:
        mock_execute.return_value = True
        
        result = await migration_manager.apply_migration(sample_migration)
        assert result is True
        mock_execute.assert_called_once()

@pytest.mark.asyncio
async def test_migration_rollback(migration_manager, sample_migration):
    with patch.object(migration_manager, '_rollback_migration') as mock_rollback:
        mock_rollback.return_value = True
        
        # Simulate failed migration
        await migration_manager.set_migration_state(
            sample_migration["name"],
            MigrationState.FAILED
        )
        
        result = await migration_manager.rollback_migration(sample_migration)
        assert result is True
        mock_rollback.assert_called_once()

@pytest.mark.asyncio
async def test_parallel_migrations(migration_manager):
    migrations = [
        {"version": "1.0.0", "name": f"migration_{i}", "up": "", "down": ""}
        for i in range(3)
    ]
    
    with patch.object(migration_manager, '_execute_migration') as mock_execute:
        mock_execute.return_value = True
        await migration_manager.apply_migrations(migrations)
        
        # Should be called for each migration
        assert mock_execute.call_count == len(migrations)

@pytest.mark.asyncio
async def test_migration_version_tracking(migration_manager, sample_migration):
    with patch.object(migration_manager, '_get_applied_versions') as mock_versions:
        mock_versions.return_value = ["1.0.0"]
        
        is_applied = await migration_manager.is_migration_applied(sample_migration)
        assert is_applied is True

@pytest.mark.asyncio
async def test_migration_checksum_validation(migration_manager, sample_migration):
    # Test with valid checksum
    with patch.object(migration_manager, '_calculate_checksum') as mock_checksum:
        mock_checksum.return_value = sample_migration["checksum"]
        assert await migration_manager.validate_migration(sample_migration)
        
        # Test with invalid checksum
        mock_checksum.return_value = "invalid_checksum"
        with pytest.raises(MigrationError):
            await migration_manager.validate_migration(sample_migration)

@pytest.mark.asyncio
async def test_migration_timeout(migration_manager, sample_migration):
    with patch.object(migration_manager, '_execute_migration') as mock_execute:
        mock_execute.side_effect = asyncio.TimeoutError()
        
        with pytest.raises(MigrationError):
            await migration_manager.apply_migration(sample_migration)

@pytest.mark.asyncio
async def test_migration_metrics(migration_manager, metrics_collector, sample_migration):
    with patch.object(migration_manager, '_execute_migration'):
        await migration_manager.apply_migration(sample_migration)
        
        metrics_collector.record_migration_duration.assert_called()
        metrics_collector.record_migration_status.assert_called() 