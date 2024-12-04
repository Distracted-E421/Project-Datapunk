import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from fastapi import HTTPException
from fastapi.testclient import TestClient

from datapunk_shared.auth.routes import (
    router,
    get_role_manager,
    Role,
    ResourcePolicy,
    Permission,
    RoleAssignment
)

@pytest.fixture
def mock_role_manager():
    """Mock RoleManager for testing routes."""
    manager = Mock()
    manager.create_role = AsyncMock()
    manager.assign_role = AsyncMock()
    manager.revoke_role = AsyncMock()
    manager.get_user_roles = AsyncMock()
    manager.create_role_with_audit = AsyncMock()
    manager.assign_role_with_audit = AsyncMock()
    return manager

@pytest.fixture
def test_client(mock_role_manager):
    """Create FastAPI test client with mocked dependencies."""
    app = TestClient(router)
    app.dependency_overrides[get_role_manager] = lambda: mock_role_manager
    return app

@pytest.fixture
def sample_role():
    """Create a sample role for testing."""
    return {
        "name": "test_role",
        "policies": [
            {
                "resource": "test_resource",
                "permissions": ["READ", "WRITE"]
            }
        ],
        "parent_roles": ["parent_role"],
        "metadata": {"description": "Test role"}
    }

@pytest.fixture
def sample_assignment():
    """Create a sample role assignment for testing."""
    return {
        "user_id": "test_user",
        "role_name": "test_role",
        "assigned_by": "admin",
        "expires_at": datetime.utcnow().isoformat(),
        "metadata": {"reason": "testing"}
    }

class TestRoleRoutes:
    async def test_create_role_success(self, test_client, mock_role_manager, sample_role):
        """Test successful role creation endpoint."""
        mock_role_manager.create_role.return_value = True
        
        response = await test_client.post(
            "/",
            json={
                "role": sample_role,
                "created_by": "admin"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["role"] == sample_role["name"]
        mock_role_manager.create_role.assert_called_once()

    async def test_create_role_failure(self, test_client, mock_role_manager, sample_role):
        """Test role creation endpoint failure handling."""
        mock_role_manager.create_role.side_effect = Exception("Creation failed")
        
        response = await test_client.post(
            "/",
            json={
                "role": sample_role,
                "created_by": "admin"
            }
        )
        
        assert response.status_code == 400
        assert "Creation failed" in response.json()["detail"]

    async def test_assign_role_success(self, test_client, mock_role_manager, sample_assignment):
        """Test successful role assignment endpoint."""
        mock_role_manager.assign_role.return_value = True
        
        response = await test_client.post("/assign", json=sample_assignment)
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_role_manager.assign_role.assert_called_once()

    async def test_assign_role_failure(self, test_client, mock_role_manager, sample_assignment):
        """Test role assignment endpoint failure handling."""
        mock_role_manager.assign_role.side_effect = Exception("Assignment failed")
        
        response = await test_client.post("/assign", json=sample_assignment)
        
        assert response.status_code == 400
        assert "Assignment failed" in response.json()["detail"]

    async def test_revoke_role_success(self, test_client, mock_role_manager):
        """Test successful role revocation endpoint."""
        mock_role_manager.revoke_role.return_value = True
        
        response = await test_client.delete(
            "/revoke/test_user/test_role",
            params={"revoked_by": "admin"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_role_manager.revoke_role.assert_called_once_with(
            "test_user", "test_role", "admin"
        )

    async def test_revoke_role_failure(self, test_client, mock_role_manager):
        """Test role revocation endpoint failure handling."""
        mock_role_manager.revoke_role.side_effect = Exception("Revocation failed")
        
        response = await test_client.delete(
            "/revoke/test_user/test_role",
            params={"revoked_by": "admin"}
        )
        
        assert response.status_code == 400
        assert "Revocation failed" in response.json()["detail"]

    async def test_get_user_roles_success(self, test_client, mock_role_manager):
        """Test successful user roles retrieval endpoint."""
        mock_roles = [
            Role(
                name="test_role",
                policies=[],
                parent_roles=[],
                metadata={}
            )
        ]
        mock_role_manager.get_user_roles.return_value = mock_roles
        
        response = await test_client.get("/user/test_user")
        
        assert response.status_code == 200
        result = response.json()
        assert result["user_id"] == "test_user"
        assert len(result["roles"]) == 1
        assert result["roles"][0]["name"] == "test_role"
        mock_role_manager.get_user_roles.assert_called_once_with("test_user")

    async def test_get_user_roles_failure(self, test_client, mock_role_manager):
        """Test user roles retrieval endpoint failure handling."""
        mock_role_manager.get_user_roles.side_effect = Exception("Fetch failed")
        
        response = await test_client.get("/user/test_user")
        
        assert response.status_code == 400
        assert "Fetch failed" in response.json()["detail"]

    async def test_create_role_with_audit_success(self, test_client, mock_role_manager, sample_role):
        """Test successful role creation with audit endpoint."""
        mock_role_manager.create_role_with_audit.return_value = True
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.session = {"session_id": "test_session"}
        
        response = await test_client.post(
            "/audit",
            json={
                "role": sample_role,
                "created_by": "admin"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_role_manager.create_role_with_audit.assert_called_once()

    async def test_assign_role_with_audit_success(self, test_client, mock_role_manager, sample_assignment):
        """Test successful role assignment with audit endpoint."""
        mock_role_manager.assign_role_with_audit.return_value = True
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.session = {"session_id": "test_session"}
        
        response = await test_client.post("/audit/assign", json=sample_assignment)
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_role_manager.assign_role_with_audit.assert_called_once() 