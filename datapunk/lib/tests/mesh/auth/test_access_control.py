import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.auth import (
    AccessControl,
    AccessConfig,
    Role,
    Permission,
    Policy,
    AccessRequest,
    AccessDenied
)

@pytest.fixture
def access_config():
    return AccessConfig(
        default_policy="deny",
        cache_ttl=300,  # 5 minutes
        max_roles_per_user=10,
        enable_audit=True
    )

@pytest.fixture
def access_control(access_config):
    return AccessControl(config=access_config)

@pytest.fixture
def sample_roles():
    return [
        Role(
            name="admin",
            permissions=["read", "write", "delete"],
            scope="global"
        ),
        Role(
            name="user",
            permissions=["read"],
            scope="user"
        ),
        Role(
            name="service",
            permissions=["read", "write"],
            scope="service"
        )
    ]

@pytest.fixture
def sample_policies():
    return [
        Policy(
            name="data_access",
            resources=["database", "storage"],
            actions=["read", "write"],
            conditions={"ip_range": "192.168.0.0/16"}
        ),
        Policy(
            name="admin_access",
            resources=["*"],
            actions=["*"],
            conditions={"environment": "production"}
        )
    ]

@pytest.mark.asyncio
async def test_access_initialization(access_control, access_config):
    assert access_control.config == access_config
    assert access_control.is_initialized
    assert len(access_control.roles) == 0
    assert len(access_control.policies) == 0

@pytest.mark.asyncio
async def test_role_management(access_control, sample_roles):
    # Add roles
    for role in sample_roles:
        await access_control.add_role(role)
    
    assert len(access_control.roles) == len(sample_roles)
    assert all(r.name in access_control.roles for r in sample_roles)

@pytest.mark.asyncio
async def test_policy_management(access_control, sample_policies):
    # Add policies
    for policy in sample_policies:
        await access_control.add_policy(policy)
    
    assert len(access_control.policies) == len(sample_policies)
    assert all(p.name in access_control.policies for p in sample_policies)

@pytest.mark.asyncio
async def test_permission_check(access_control, sample_roles):
    role = sample_roles[0]  # admin role
    await access_control.add_role(role)
    
    # Check permission
    has_permission = await access_control.check_permission(
        role_name="admin",
        permission="write"
    )
    
    assert has_permission

@pytest.mark.asyncio
async def test_access_request(access_control, sample_roles, sample_policies):
    # Setup roles and policies
    await access_control.add_role(sample_roles[0])  # admin role
    await access_control.add_policy(sample_policies[0])  # data_access policy
    
    # Create access request
    request = AccessRequest(
        user_id="user123",
        role="admin",
        resource="database",
        action="write",
        context={"ip": "192.168.1.100"}
    )
    
    # Check access
    access_granted = await access_control.check_access(request)
    assert access_granted

@pytest.mark.asyncio
async def test_role_inheritance(access_control):
    # Create roles with inheritance
    base_role = Role(
        name="base",
        permissions=["read"],
        scope="global"
    )
    
    derived_role = Role(
        name="derived",
        permissions=["write"],
        scope="global",
        inherits=["base"]
    )
    
    await access_control.add_role(base_role)
    await access_control.add_role(derived_role)
    
    # Check inherited permissions
    has_permission = await access_control.check_permission(
        role_name="derived",
        permission="read"
    )
    
    assert has_permission

@pytest.mark.asyncio
async def test_policy_evaluation(access_control, sample_policies):
    policy = sample_policies[0]  # data_access policy
    await access_control.add_policy(policy)
    
    # Evaluate policy
    result = await access_control.evaluate_policy(
        policy_name="data_access",
        context={
            "resource": "database",
            "action": "read",
            "ip_range": "192.168.1.100"
        }
    )
    
    assert result.allowed
    assert result.policy_name == "data_access"

@pytest.mark.asyncio
async def test_role_assignment(access_control, sample_roles):
    role = sample_roles[1]  # user role
    await access_control.add_role(role)
    
    # Assign role to user
    await access_control.assign_role(
        user_id="user123",
        role_name="user"
    )
    
    # Check user roles
    user_roles = await access_control.get_user_roles("user123")
    assert "user" in user_roles

@pytest.mark.asyncio
async def test_policy_conditions(access_control):
    # Create policy with conditions
    policy = Policy(
        name="time_based",
        resources=["api"],
        actions=["access"],
        conditions={
            "time_range": {
                "start": "09:00",
                "end": "17:00"
            }
        }
    )
    
    await access_control.add_policy(policy)
    
    # Test with different times
    with patch('datetime.datetime') as mock_datetime:
        # During allowed hours
        mock_datetime.now.return_value = datetime.strptime("14:00", "%H:%M")
        
        result = await access_control.evaluate_policy(
            policy_name="time_based",
            context={"resource": "api", "action": "access"}
        )
        assert result.allowed
        
        # Outside allowed hours
        mock_datetime.now.return_value = datetime.strptime("20:00", "%H:%M")
        
        result = await access_control.evaluate_policy(
            policy_name="time_based",
            context={"resource": "api", "action": "access"}
        )
        assert not result.allowed

@pytest.mark.asyncio
async def test_access_caching(access_control, sample_roles):
    role = sample_roles[0]  # admin role
    await access_control.add_role(role)
    
    # First access check
    request = AccessRequest(
        user_id="user123",
        role="admin",
        resource="database",
        action="write",
        context={}
    )
    
    await access_control.check_access(request)
    
    # Second access check should use cache
    with patch.object(access_control, '_evaluate_access') as mock_evaluate:
        await access_control.check_access(request)
        mock_evaluate.assert_not_called()

@pytest.mark.asyncio
async def test_concurrent_access_checks(access_control, sample_roles, sample_policies):
    # Setup roles and policies
    await access_control.add_role(sample_roles[0])
    await access_control.add_policy(sample_policies[0])
    
    # Generate multiple access requests
    requests = [
        AccessRequest(
            user_id=f"user{i}",
            role="admin",
            resource="database",
            action="read",
            context={"ip": "192.168.1.100"}
        )
        for i in range(100)
    ]
    
    # Check access concurrently
    results = await asyncio.gather(*[
        access_control.check_access(request)
        for request in requests
    ])
    
    assert all(results)

@pytest.mark.asyncio
async def test_role_revocation(access_control, sample_roles):
    role = sample_roles[1]  # user role
    await access_control.add_role(role)
    
    # Assign and then revoke role
    user_id = "user123"
    await access_control.assign_role(user_id, role.name)
    await access_control.revoke_role(user_id, role.name)
    
    user_roles = await access_control.get_user_roles(user_id)
    assert role.name not in user_roles

@pytest.mark.asyncio
async def test_policy_updates(access_control, sample_policies):
    policy = sample_policies[0]
    await access_control.add_policy(policy)
    
    # Update policy
    updated_policy = Policy(
        name=policy.name,
        resources=policy.resources + ["logs"],
        actions=policy.actions,
        conditions=policy.conditions
    )
    
    await access_control.update_policy(updated_policy)
    
    stored_policy = access_control.policies[policy.name]
    assert "logs" in stored_policy.resources

@pytest.mark.asyncio
async def test_access_audit(access_control, sample_roles):
    with patch('datapunk_shared.mesh.audit.AuditLogger') as mock_logger:
        role = sample_roles[0]
        await access_control.add_role(role)
        
        request = AccessRequest(
            user_id="user123",
            role="admin",
            resource="database",
            action="write",
            context={}
        )
        
        await access_control.check_access(request)
        
        mock_logger.return_value.log_access_check.assert_called_once()

@pytest.mark.asyncio
async def test_invalid_access(access_control):
    # Test with non-existent role
    request = AccessRequest(
        user_id="user123",
        role="nonexistent",
        resource="database",
        action="write",
        context={}
    )
    
    with pytest.raises(AccessDenied):
        await access_control.check_access(request) 