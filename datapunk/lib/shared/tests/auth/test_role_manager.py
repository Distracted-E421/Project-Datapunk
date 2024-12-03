import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import json

from datapunk_shared.auth.role_manager import (
    RoleManager,
    RoleAssignment,
    Role,
    ResourcePolicy,
    Permission,
    AuthError
)

@pytest.fixture
def mock_cache():
    """Mock cache client for testing."""
    cache = Mock()
    cache.set = AsyncMock()
    cache.get = AsyncMock()
    cache.delete = AsyncMock()
    cache.exists = AsyncMock()
    cache.scan = AsyncMock()
    return cache

@pytest.fixture
def mock_metrics():
    """Mock metrics client for testing."""
    metrics = Mock()
    metrics.increment = Mock()
    return metrics

@pytest.fixture
def mock_audit_logger():
    """Mock audit logger for testing."""
    return Mock()

@pytest.fixture
def role_manager(mock_cache, mock_metrics, mock_audit_logger):
    """Create RoleManager instance with mocked dependencies."""
    return RoleManager(mock_cache, mock_metrics, mock_audit_logger)

@pytest.fixture
def sample_role():
    """Create a sample role for testing."""
    return Role(
        name="test_role",
        policies=[
            ResourcePolicy(
                resource="test_resource",
                permissions=[Permission.READ, Permission.WRITE]
            )
        ],
        parent_roles=["parent_role"],
        metadata={"description": "Test role"}
    )

@pytest.fixture
def sample_assignment():
    """Create a sample role assignment for testing."""
    return RoleAssignment(
        user_id="test_user",
        role_name="test_role",
        assigned_by="admin",
        assigned_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
        metadata={"reason": "testing"}
    )

class TestRoleManager:
    @pytest.mark.asyncio
    async def test_create_role_success(self, role_manager, mock_cache, sample_role):
        """Test successful role creation."""
        mock_cache.exists.return_value = False
        
        result = await role_manager.create_role(sample_role, "admin")
        
        assert result is True
        mock_cache.set.assert_called_once()
        mock_cache.exists.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_role_already_exists(self, role_manager, mock_cache, sample_role):
        """Test role creation when role already exists."""
        mock_cache.exists.return_value = True
        
        with pytest.raises(AuthError):
            await role_manager.create_role(sample_role, "admin")

    @pytest.mark.asyncio
    async def test_assign_role_success(self, role_manager, mock_cache, sample_assignment):
        """Test successful role assignment."""
        mock_cache.exists.return_value = True
        
        result = await role_manager.assign_role(sample_assignment)
        
        assert result is True
        mock_cache.set.assert_called()
        mock_cache.exists.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_role_nonexistent(self, role_manager, mock_cache, sample_assignment):
        """Test role assignment with non-existent role."""
        mock_cache.exists.return_value = False
        
        with pytest.raises(AuthError):
            await role_manager.assign_role(sample_assignment)

    @pytest.mark.asyncio
    async def test_revoke_role_success(self, role_manager, mock_cache):
        """Test successful role revocation."""
        mock_cache.delete.return_value = True
        
        result = await role_manager.revoke_role("test_user", "test_role", "admin")
        
        assert result is True
        mock_cache.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_role_nonexistent(self, role_manager, mock_cache):
        """Test role revocation for non-existent assignment."""
        mock_cache.delete.return_value = False
        
        result = await role_manager.revoke_role("test_user", "test_role", "admin")
        
        assert result is False
        mock_cache.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_roles_from_cache(self, role_manager, mock_cache):
        """Test retrieving user roles from cache."""
        cached_roles = [
            {
                "name": "test_role",
                "policies": [],
                "parent_roles": [],
                "metadata": {}
            }
        ]
        mock_cache.get.return_value = json.dumps(cached_roles)
        
        roles = await role_manager.get_user_roles("test_user")
        
        assert len(roles) == 1
        assert roles[0].name == "test_role"
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_roles_rebuild_cache(self, role_manager, mock_cache):
        """Test rebuilding user roles when cache miss."""
        mock_cache.get.return_value = None
        mock_cache.scan.return_value = ["role:assignment:test_user:test_role"]
        
        role_data = {
            "name": "test_role",
            "policies": [],
            "parent_roles": [],
            "metadata": {}
        }
        mock_cache.get.side_effect = [None, json.dumps(role_data)]
        
        roles = await role_manager.get_user_roles("test_user")
        
        assert len(roles) == 1
        assert roles[0].name == "test_role"
        assert mock_cache.scan.called
        assert mock_cache.set.called

    @pytest.mark.asyncio
    async def test_role_exists(self, role_manager, mock_cache):
        """Test role existence check."""
        mock_cache.exists.return_value = True
        
        result = await role_manager._role_exists("test_role")
        
        assert result is True
        mock_cache.exists.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_role(self, role_manager, mock_cache):
        """Test retrieving role details."""
        role_data = {
            "name": "test_role",
            "policies": [],
            "parent_roles": [],
            "metadata": {}
        }
        mock_cache.get.return_value = json.dumps(role_data)
        
        role = await role_manager._get_role("test_role")
        
        assert role is not None
        assert role.name == "test_role"
        mock_cache.get.assert_called_once() 