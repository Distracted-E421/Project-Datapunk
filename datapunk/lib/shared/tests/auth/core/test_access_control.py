"""
Core Access Control Tests
--------------------

Tests the core access control system including:
- Permission management
- Role-based access control (RBAC)
- Resource permissions
- Access validation
- Policy enforcement
- Inheritance rules
- Security controls

Run with: pytest -v test_access_control.py
"""

import pytest
from datetime import datetime
import json
from unittest.mock import AsyncMock, Mock, patch

from datapunk_shared.auth.core.access_control import (
    AccessManager,
    Permission,
    Role,
    Resource,
    Policy,
    AccessRule,
    AccessContext
)
from datapunk_shared.auth.core.exceptions import PermissionError

# Test Fixtures

@pytest.fixture
def storage_client():
    """Mock storage client for testing."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.store = AsyncMock()
    client.list = AsyncMock()
    return client

@pytest.fixture
def cache_client():
    """Mock cache client for testing."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.set = AsyncMock()
    client.delete = AsyncMock()
    return client

@pytest.fixture
def access_manager(storage_client, cache_client):
    """Create access manager for testing."""
    return AccessManager(
        storage=storage_client,
        cache=cache_client
    )

@pytest.fixture
def test_role():
    """Create test role for testing."""
    return Role(
        name="test_role",
        permissions=[
            Permission("read", "document"),
            Permission("write", "document")
        ],
        metadata={
            "description": "Test role"
        }
    )

@pytest.fixture
def test_policy():
    """Create test policy for testing."""
    return Policy(
        name="test_policy",
        rules=[
            AccessRule("allow", "read", "document"),
            AccessRule("deny", "delete", "document")
        ],
        priority=1
    )

# Permission Tests

def test_permission_creation():
    """Test permission creation."""
    perm = Permission("read", "document")
    
    assert perm.action == "read"
    assert perm.resource == "document"
    assert perm.is_valid()

def test_permission_validation():
    """Test permission validation."""
    # Invalid action
    with pytest.raises(ValueError):
        Permission("", "document")
    
    # Invalid resource
    with pytest.raises(ValueError):
        Permission("read", "")
    
    # Valid wildcard
    perm = Permission("*", "document")
    assert perm.is_valid()
    assert perm.is_wildcard_action()

# Role Tests

def test_role_creation(test_role):
    """Test role creation."""
    assert test_role.name == "test_role"
    assert len(test_role.permissions) == 2
    assert test_role.metadata["description"] == "Test role"

def test_role_permission_management(test_role):
    """Test role permission management."""
    # Add permission
    test_role.add_permission(Permission("delete", "document"))
    assert len(test_role.permissions) == 3
    
    # Remove permission
    test_role.remove_permission("write", "document")
    assert len(test_role.permissions) == 2
    
    # Check permission
    assert test_role.has_permission("read", "document")
    assert not test_role.has_permission("write", "document")

def test_role_inheritance():
    """Test role inheritance."""
    parent_role = Role(
        name="parent",
        permissions=[Permission("read", "document")]
    )
    
    child_role = Role(
        name="child",
        permissions=[Permission("write", "document")],
        inherit_from=parent_role
    )
    
    assert child_role.has_permission("read", "document")
    assert child_role.has_permission("write", "document")

# Policy Tests

def test_policy_creation(test_policy):
    """Test policy creation."""
    assert test_policy.name == "test_policy"
    assert len(test_policy.rules) == 2
    assert test_policy.priority == 1

def test_policy_evaluation(test_policy):
    """Test policy evaluation."""
    # Allowed action
    assert test_policy.allows("read", "document")
    
    # Denied action
    assert not test_policy.allows("delete", "document")
    
    # Undefined action (default deny)
    assert not test_policy.allows("update", "document")

def test_policy_priority():
    """Test policy priority resolution."""
    policy1 = Policy(
        name="policy1",
        rules=[AccessRule("allow", "read", "document")],
        priority=1
    )
    
    policy2 = Policy(
        name="policy2",
        rules=[AccessRule("deny", "read", "document")],
        priority=2
    )
    
    # Higher priority should win
    assert not Policy.resolve([policy1, policy2], "read", "document")

# Access Manager Tests

@pytest.mark.asyncio
async def test_access_validation(access_manager, test_role, test_policy):
    """Test access validation."""
    # Setup mock data
    access_manager.storage.get.side_effect = {
        "role:test_role": test_role.to_dict(),
        "policy:test_policy": test_policy.to_dict()
    }.get
    
    # Test allowed access
    result = await access_manager.validate_access(
        user_id="test_user",
        action="read",
        resource="document",
        roles=["test_role"]
    )
    assert result.allowed is True
    
    # Test denied access
    result = await access_manager.validate_access(
        user_id="test_user",
        action="delete",
        resource="document",
        roles=["test_role"]
    )
    assert result.allowed is False

@pytest.mark.asyncio
async def test_role_assignment(access_manager, test_role):
    """Test role assignment."""
    # Assign role
    await access_manager.assign_role("test_user", test_role.name)
    
    # Verify storage
    access_manager.storage.store.assert_called_with(
        f"user_roles:test_user",
        {"roles": [test_role.name]}
    )
    
    # Verify cache invalidation
    access_manager.cache.delete.assert_called_with(
        f"user_permissions:test_user"
    )

@pytest.mark.asyncio
async def test_permission_caching(access_manager, test_role):
    """Test permission caching."""
    # Setup mock data
    access_manager.storage.get.return_value = test_role.to_dict()
    access_manager.cache.get.return_value = None
    
    # First access (should cache)
    result1 = await access_manager.get_user_permissions("test_user")
    assert access_manager.cache.set.called
    
    # Second access (should use cache)
    access_manager.cache.get.return_value = result1
    result2 = await access_manager.get_user_permissions("test_user")
    assert result1 == result2
    assert access_manager.storage.get.call_count == 1

# Resource Tests

def test_resource_hierarchy():
    """Test resource hierarchy."""
    parent = Resource("documents")
    child = Resource("reports", parent=parent)
    
    assert child.is_child_of(parent)
    assert parent.is_parent_of(child)
    assert child.get_full_path() == "documents/reports"

def test_resource_permissions():
    """Test resource-specific permissions."""
    resource = Resource(
        name="confidential_docs",
        required_permissions=[
            Permission("read", "confidential"),
            Permission("write", "confidential")
        ]
    )
    
    assert resource.requires_permission("read")
    assert resource.requires_permission("write")
    assert not resource.requires_permission("delete")

# Security Tests

@pytest.mark.asyncio
async def test_access_logging(access_manager):
    """Test access logging."""
    context = AccessContext(
        user_id="test_user",
        action="read",
        resource="document",
        timestamp=datetime.utcnow()
    )
    
    await access_manager.log_access(context)
    
    # Verify audit log
    access_manager.audit_logger.log.assert_called_with({
        "type": "access_control",
        "user_id": "test_user",
        "action": "read",
        "resource": "document",
        "timestamp": context.timestamp.isoformat()
    })

@pytest.mark.asyncio
async def test_security_controls(access_manager):
    """Test security controls."""
    # Enable security mode
    access_manager.enable_security()
    
    # Test sensitive resource access
    with pytest.raises(PermissionError) as exc:
        await access_manager.validate_access(
            user_id="test_user",
            action="read",
            resource="sensitive_data",
            roles=["basic_role"]
        )
    assert "insufficient privileges" in str(exc.value)

# Performance Tests

@pytest.mark.asyncio
async def test_bulk_validation(access_manager):
    """Test bulk access validation."""
    requests = [
        {
            "user_id": "test_user",
            "action": "read",
            "resource": "document"
        }
        for _ in range(100)
    ]
    
    start_time = datetime.utcnow()
    results = await access_manager.validate_bulk_access(requests)
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 1.0  # Should validate 100 requests within 1 second
    
    # Verify results
    assert len(results) == 100
    assert all(isinstance(r.allowed, bool) for r in results)

@pytest.mark.asyncio
async def test_cache_performance(access_manager):
    """Test cache performance."""
    # Warm up cache
    await access_manager.get_user_permissions("test_user")
    
    # Test cached access
    start_time = datetime.utcnow()
    for _ in range(1000):
        await access_manager.get_user_permissions("test_user")
    end_time = datetime.utcnow()
    
    # Verify timing
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 1.0  # Should handle 1000 cached lookups within 1 second 