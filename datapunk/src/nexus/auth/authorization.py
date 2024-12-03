from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import re

class Permission(Enum):
    # Resource access
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    
    # Administrative
    ADMIN = "admin"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    AUDIT = "audit"
    
    # Service specific
    MANAGE_SERVICES = "manage_services"
    VIEW_METRICS = "view_metrics"
    MANAGE_POLICIES = "manage_policies"

@dataclass
class Role:
    name: str
    description: str
    permissions: Set[Permission]
    parent_roles: Set[str] = field(default_factory=set)

@dataclass
class Policy:
    name: str
    description: str
    resource_pattern: str  # Regex pattern for resource matching
    required_permissions: Set[Permission]
    deny_permissions: Set[Permission] = field(default_factory=set)
    require_all: bool = False  # If True, all permissions are required; if False, any permission is sufficient

class AuthorizationManager:
    def __init__(self):
        self._roles: Dict[str, Role] = {}
        self._policies: Dict[str, Policy] = {}
        self._user_roles: Dict[str, Set[str]] = {}
        
        # Initialize default roles
        self._initialize_default_roles()
        
    def _initialize_default_roles(self):
        """Initialize default system roles."""
        # Super Admin role
        self.create_role(
            "super_admin",
            "Full system access",
            {perm for perm in Permission}
        )
        
        # Service Admin role
        self.create_role(
            "service_admin",
            "Service management access",
            {
                Permission.READ,
                Permission.WRITE,
                Permission.EXECUTE,
                Permission.MANAGE_SERVICES,
                Permission.VIEW_METRICS
            }
        )
        
        # Auditor role
        self.create_role(
            "auditor",
            "Audit and monitoring access",
            {
                Permission.READ,
                Permission.AUDIT,
                Permission.VIEW_METRICS
            }
        )
        
    def create_role(self, name: str, description: str, permissions: Set[Permission], parent_roles: Set[str] = None) -> Role:
        """Create a new role with specified permissions."""
        if name in self._roles:
            raise ValueError(f"Role {name} already exists")
            
        role = Role(
            name=name,
            description=description,
            permissions=permissions,
            parent_roles=parent_roles or set()
        )
        self._roles[name] = role
        return role
        
    def get_role(self, name: str) -> Optional[Role]:
        """Get role by name."""
        return self._roles.get(name)
        
    def assign_role_to_user(self, user_id: str, role_name: str):
        """Assign a role to a user."""
        if role_name not in self._roles:
            raise ValueError(f"Role {role_name} does not exist")
            
        if user_id not in self._user_roles:
            self._user_roles[user_id] = set()
            
        self._user_roles[user_id].add(role_name)
        
    def get_user_roles(self, user_id: str) -> Set[str]:
        """Get all roles assigned to a user."""
        return self._user_roles.get(user_id, set())
        
    def get_effective_permissions(self, user_id: str) -> Set[Permission]:
        """Get all effective permissions for a user including inherited permissions."""
        permissions = set()
        roles = self.get_user_roles(user_id)
        
        def add_role_permissions(role_name: str, visited: Set[str]):
            if role_name in visited:
                return
                
            visited.add(role_name)
            role = self._roles.get(role_name)
            if role:
                permissions.update(role.permissions)
                for parent in role.parent_roles:
                    add_role_permissions(parent, visited)
                    
        for role_name in roles:
            add_role_permissions(role_name, set())
            
        return permissions
        
    def create_policy(self, name: str, description: str, resource_pattern: str,
                     required_permissions: Set[Permission], deny_permissions: Set[Permission] = None,
                     require_all: bool = False) -> Policy:
        """Create a new access policy."""
        if name in self._policies:
            raise ValueError(f"Policy {name} already exists")
            
        policy = Policy(
            name=name,
            description=description,
            resource_pattern=resource_pattern,
            required_permissions=required_permissions,
            deny_permissions=deny_permissions or set(),
            require_all=require_all
        )
        self._policies[name] = policy
        return policy
        
    def check_permission(self, user_id: str, resource: str, required_permission: Permission) -> bool:
        """Check if user has permission to access a resource."""
        user_permissions = self.get_effective_permissions(user_id)
        
        # Super admin has all permissions
        if Permission.ADMIN in user_permissions:
            return True
            
        # Check if user has the required permission
        if required_permission not in user_permissions:
            return False
            
        # Check policies
        for policy in self._policies.values():
            if re.match(policy.resource_pattern, resource):
                # Check deny permissions first
                if required_permission in policy.deny_permissions:
                    return False
                    
                # Check required permissions
                if policy.require_all:
                    if not policy.required_permissions.issubset(user_permissions):
                        return False
                else:
                    if not any(perm in user_permissions for perm in policy.required_permissions):
                        return False
                        
        return True
        
    def check_permissions(self, user_id: str, resource: str, required_permissions: Set[Permission], require_all: bool = True) -> bool:
        """Check if user has multiple permissions to access a resource."""
        if require_all:
            return all(self.check_permission(user_id, resource, perm) for perm in required_permissions)
        else:
            return any(self.check_permission(user_id, resource, perm) for perm in required_permissions) 