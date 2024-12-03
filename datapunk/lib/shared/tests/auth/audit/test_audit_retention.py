"""
Audit Retention Tests
----------------

Tests the audit retention system including:
- Retention policy management
- Data lifecycle
- Archival process
- Cleanup operations
- Compliance rules
- Performance monitoring
- Security controls

Run with: pytest -v test_audit_retention.py
"""

import pytest
from datetime import datetime, timedelta
import json
from unittest.mock import AsyncMock, Mock, patch

from datapunk_shared.auth.audit.audit_retention import (
    RetentionManager,
    RetentionPolicy,
    RetentionRule,
    ArchiveManager,
    RetentionMetrics,
    RetentionStatus
)

# Test Fixtures

@pytest.fixture
def storage_client():
    """Mock storage client for testing."""
    client = AsyncMock()
    client.archive = AsyncMock()
    client.delete = AsyncMock()
    client.list = AsyncMock()
    return client

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.gauge = AsyncMock()
    client.timing = AsyncMock()
    return client

@pytest.fixture
def retention_policy():
    """Create retention policy for testing."""
    return RetentionPolicy(
        default_ttl=timedelta(days=90),
        rules=[
            RetentionRule(
                category="security",
                ttl=timedelta(days=365)
            ),
            RetentionRule(
                category="debug",
                ttl=timedelta(days=30)
            )
        ]
    )

@pytest.fixture
def retention_manager(storage_client, metrics_client, retention_policy):
    """Create retention manager for testing."""
    return RetentionManager(
        storage=storage_client,
        metrics=metrics_client,
        policy=retention_policy
    )

# Policy Management Tests

def test_policy_creation():
    """Test retention policy creation."""
    policy = RetentionPolicy(
        default_ttl=timedelta(days=90),
        rules=[
            RetentionRule(category="test", ttl=timedelta(days=30))
        ]
    )
    
    assert policy.default_ttl.days == 90
    assert len(policy.rules) == 1
    assert policy.rules[0].category == "test"
    assert policy.rules[0].ttl.days == 30

def test_policy_validation():
    """Test retention policy validation."""
    # Invalid TTL
    with pytest.raises(ValueError):
        RetentionPolicy(default_ttl=timedelta(days=-1))
    
    # Duplicate categories
    with pytest.raises(ValueError):
        RetentionPolicy(
            default_ttl=timedelta(days=90),
            rules=[
                RetentionRule(category="test", ttl=timedelta(days=30)),
                RetentionRule(category="test", ttl=timedelta(days=60))
            ]
        )

def test_rule_resolution(retention_policy):
    """Test retention rule resolution."""
    # Security category
    ttl = retention_policy.get_ttl("security")
    assert ttl.days == 365
    
    # Debug category
    ttl = retention_policy.get_ttl("debug")
    assert ttl.days == 30
    
    # Unknown category (default)
    ttl = retention_policy.get_ttl("unknown")
    assert ttl.days == 90

# Data Lifecycle Tests

@pytest.mark.asyncio
async def test_data_lifecycle(retention_manager):
    """Test data lifecycle management."""
    # Mock data
    data = {
        "id": "test_id",
        "category": "security",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Process data
    result = await retention_manager.process_data(data)
    
    assert result.success is True
    assert result.ttl.days == 365  # Security category TTL
    
    # Verify storage calls
    retention_manager.storage.store.assert_called_once()
    stored_data = retention_manager.storage.store.call_args[0][0]
    assert stored_data["ttl"] == 365 * 24 * 3600  # TTL in seconds

@pytest.mark.asyncio
async def test_expiration_check(retention_manager):
    """Test data expiration checking."""
    # Mock expired data
    expired_data = {
        "id": "expired_id",
        "timestamp": (datetime.utcnow() - timedelta(days=100)).isoformat(),
        "category": "debug"  # 30 day TTL
    }
    
    is_expired = await retention_manager.is_expired(expired_data)
    assert is_expired is True
    
    # Mock active data
    active_data = {
        "id": "active_id",
        "timestamp": datetime.utcnow().isoformat(),
        "category": "security"  # 365 day TTL
    }
    
    is_expired = await retention_manager.is_expired(active_data)
    assert is_expired is False

# Archival Tests

@pytest.mark.asyncio
async def test_archival_process(retention_manager):
    """Test data archival process."""
    # Mock data for archival
    data = {
        "id": "archive_id",
        "category": "security",
        "timestamp": (datetime.utcnow() - timedelta(days=300)).isoformat()
    }
    
    # Archive data
    result = await retention_manager.archive_data(data)
    
    assert result.success is True
    assert result.archive_id is not None
    
    # Verify archive storage
    retention_manager.storage.archive.assert_called_once()
    archived_data = retention_manager.storage.archive.call_args[0][0]
    assert archived_data["id"] == "archive_id"
    assert archived_data["archive_timestamp"] is not None

@pytest.mark.asyncio
async def test_batch_archival(retention_manager):
    """Test batch archival process."""
    # Create batch of data
    batch = [
        {
            "id": f"id_{i}",
            "category": "debug",
            "timestamp": (datetime.utcnow() - timedelta(days=60)).isoformat()
        }
        for i in range(100)
    ]
    
    # Process batch
    results = await retention_manager.archive_batch(batch)
    
    assert len(results) == 100
    assert all(r.success for r in results)
    
    # Verify batch optimization
    assert retention_manager.storage.archive.call_count < 10  # Should use batching

# Cleanup Tests

@pytest.mark.asyncio
async def test_cleanup_process(retention_manager):
    """Test data cleanup process."""
    # Mock expired data
    retention_manager.storage.list.return_value = [
        {
            "id": "expired_1",
            "timestamp": (datetime.utcnow() - timedelta(days=100)).isoformat(),
            "category": "debug"
        },
        {
            "id": "expired_2",
            "timestamp": (datetime.utcnow() - timedelta(days=100)).isoformat(),
            "category": "debug"
        }
    ]
    
    # Run cleanup
    result = await retention_manager.cleanup()
    
    assert result.success is True
    assert result.items_processed == 2
    assert result.items_deleted == 2
    
    # Verify deletion calls
    assert retention_manager.storage.delete.call_count == 2

@pytest.mark.asyncio
async def test_selective_cleanup(retention_manager):
    """Test selective data cleanup."""
    # Mock mixed data
    retention_manager.storage.list.return_value = [
        {
            "id": "keep_1",
            "timestamp": datetime.utcnow().isoformat(),
            "category": "security"
        },
        {
            "id": "delete_1",
            "timestamp": (datetime.utcnow() - timedelta(days=100)).isoformat(),
            "category": "debug"
        }
    ]
    
    # Run cleanup
    result = await retention_manager.cleanup()
    
    assert result.success is True
    assert result.items_processed == 2
    assert result.items_deleted == 1  # Only expired items
    
    # Verify correct item deleted
    retention_manager.storage.delete.assert_called_once_with("delete_1")

# Performance Tests

@pytest.mark.asyncio
async def test_cleanup_performance(retention_manager):
    """Test cleanup performance."""
    # Mock large dataset
    retention_manager.storage.list.return_value = [
        {
            "id": f"id_{i}",
            "timestamp": (datetime.utcnow() - timedelta(days=100)).isoformat(),
            "category": "debug"
        }
        for i in range(1000)
    ]
    
    # Run cleanup
    start_time = datetime.utcnow()
    result = await retention_manager.cleanup()
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 5.0  # Should process 1000 items within 5 seconds
    
    # Verify batch optimization
    assert retention_manager.storage.delete.call_count < 20  # Should use batching

@pytest.mark.asyncio
async def test_metrics_collection(retention_manager):
    """Test metrics collection."""
    # Process some data
    await retention_manager.process_data({
        "id": "test_id",
        "category": "security"
    })
    
    # Verify metrics
    retention_manager.metrics.increment.assert_has_calls([
        mock.call("retention_items_processed", tags={"category": "security"}),
        mock.call("retention_ttl_set", tags={"ttl": "365"})
    ])
    
    # Run cleanup
    await retention_manager.cleanup()
    
    # Verify cleanup metrics
    retention_manager.metrics.gauge.assert_called_with(
        "retention_items_cleaned",
        mock.ANY
    )

# Security Tests

@pytest.mark.asyncio
async def test_secure_cleanup(retention_manager):
    """Test secure data cleanup."""
    # Enable secure mode
    retention_manager.enable_secure_cleanup()
    
    # Mock sensitive data
    data = {
        "id": "sensitive_id",
        "category": "security",
        "content": {
            "pii": True,
            "data": "sensitive_info"
        }
    }
    
    # Process cleanup
    await retention_manager.secure_cleanup(data)
    
    # Verify secure deletion
    retention_manager.storage.secure_delete.assert_called_once()
    deleted_data = retention_manager.storage.secure_delete.call_args[0][0]
    assert deleted_data["id"] == "sensitive_id"
    assert "content" not in str(deleted_data)  # Content should be scrubbed 