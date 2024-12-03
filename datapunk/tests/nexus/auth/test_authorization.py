import pytest
from src.nexus.auth.authorization import (
    AuthorizationManager,
    Permission,
    Role,
    Policy
)

@pytest.fixture
def auth_manager():
    return AuthorizationManager()

def test_default_roles(auth_manager):
    # Check super_admin role
    super_admin = auth_manager.get_role("super_admin")
    assert super_admin is not None
    assert super_admin.name == "super_admin"
    assert len(super_admin.permissions) == len(Permission)
    
    # Check service_admin role
    service_admin = auth_manager.get_role("service_admin")
    assert service_admin is not None
    assert Permission.MANAGE_SERVICES in service_admin.permissions
    assert Permission.VIEW_METRICS in service_admin.permissions
    
    # Check auditor role
    auditor = auth_manager.get_role("auditor")
    assert auditor is not None
    assert Permission.AUDIT in auditor.permissions
    assert Permission.VIEW_METRICS in auditor.permissions

def test_create_role(auth_manager):
    # Create a custom role
    custom_role = auth_manager.create_role(
        "custom_role",
        "Custom role for testing",
        {Permission.READ, Permission.WRITE}
    )
    
    assert custom_role.name == "custom_role"
    assert custom_role.permissions == {Permission.READ, Permission.WRITE}
    
    # Try creating duplicate role
    with pytest.raises(ValueError):
        auth_manager.create_role("custom_role", "Duplicate", set())

def test_role_inheritance(auth_manager):
    # Create parent role
    parent_role = auth_manager.create_role(
        "parent_role",
        "Parent role",
        {Permission.READ}
    )
    
    # Create child role
    child_role = auth_manager.create_role(
        "child_role",
        "Child role",
        {Permission.WRITE},
        parent_roles={"parent_role"}
    )
    
    # Assign child role to user
    user_id = "test_user"
    auth_manager.assign_role_to_user(user_id, "child_role")
    
    # Check effective permissions
    permissions = auth_manager.get_effective_permissions(user_id)
    assert Permission.READ in permissions  # Inherited from parent
    assert Permission.WRITE in permissions  # Direct permission

def test_policy_enforcement(auth_manager):
    # Create role with permissions
    auth_manager.create_role(
        "api_user",
        "API User",
        {Permission.READ, Permission.WRITE}
    )
    
    # Create policy
    auth_manager.create_policy(
        "api_access",
        "API Access Policy",
        r"^/api/.*",  # Matches all paths starting with /api/
        {Permission.READ},
        deny_permissions={Permission.DELETE}
    )
    
    # Assign role to user
    user_id = "test_user"
    auth_manager.assign_role_to_user(user_id, "api_user")
    
    # Test permissions
    assert auth_manager.check_permission(user_id, "/api/data", Permission.READ)
    assert auth_manager.check_permission(user_id, "/api/data", Permission.WRITE)
    assert not auth_manager.check_permission(user_id, "/api/data", Permission.DELETE)

def test_super_admin_override(auth_manager):
    user_id = "admin_user"
    auth_manager.assign_role_to_user(user_id, "super_admin")
    
    # Super admin should have access to everything
    assert auth_manager.check_permission(user_id, "/any/resource", Permission.READ)
    assert auth_manager.check_permission(user_id, "/any/resource", Permission.WRITE)
    assert auth_manager.check_permission(user_id, "/any/resource", Permission.DELETE)
    assert auth_manager.check_permission(user_id, "/any/resource", Permission.ADMIN)

def test_multiple_permissions(auth_manager):
    # Create role with multiple permissions
    auth_manager.create_role(
        "power_user",
        "Power User",
        {Permission.READ, Permission.WRITE, Permission.EXECUTE}
    )
    
    user_id = "test_user"
    auth_manager.assign_role_to_user(user_id, "power_user")
    
    # Test checking multiple permissions
    assert auth_manager.check_permissions(
        user_id,
        "/api/data",
        {Permission.READ, Permission.WRITE},
        require_all=True
    )
    
    assert auth_manager.check_permissions(
        user_id,
        "/api/data",
        {Permission.READ, Permission.DELETE},
        require_all=False  # Only one permission needed
    )
    
    assert not auth_manager.check_permissions(
        user_id,
        "/api/data",
        {Permission.READ, Permission.DELETE},
        require_all=True  # All permissions needed
    )

def test_policy_require_all(auth_manager):
    # Create role with permissions
    auth_manager.create_role(
        "data_scientist",
        "Data Scientist",
        {Permission.READ, Permission.WRITE, Permission.EXECUTE}
    )
    
    # Create policy requiring all permissions
    auth_manager.create_policy(
        "data_access",
        "Data Access Policy",
        r"^/data/.*",
        {Permission.READ, Permission.EXECUTE},
        require_all=True
    )
    
    user_id = "test_user"
    auth_manager.assign_role_to_user(user_id, "data_scientist")
    
    # User should have access (has all required permissions)
    assert auth_manager.check_permission(user_id, "/data/analysis", Permission.READ)
    
    # Remove EXECUTE permission and create new role
    auth_manager._roles["data_scientist"].permissions.remove(Permission.EXECUTE)
    
    # User should not have access (missing EXECUTE permission)
    assert not auth_manager.check_permission(user_id, "/data/analysis", Permission.READ) 