from typing import Dict, List, Optional, Set
import structlog
from dataclasses import dataclass
import json
from datetime import datetime
from .core.access_control import Role, ResourcePolicy, Permission
from ..cache import CacheClient
from ..monitoring import MetricsClient
from ..exceptions import AuthError
from .audit.audit import AuditEvent, AuditLogger

logger = structlog.get_logger()

@dataclass
class RoleAssignment:
    """Role assignment details."""
    user_id: str
    role_name: str
    assigned_by: str
    assigned_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict] = None

class RoleManager:
    """Manages role definitions and assignments."""
    
    def __init__(self,
                 cache_client: CacheClient,
                 metrics: MetricsClient,
                 audit_logger: AuditLogger):
        self.cache = cache_client
        self.metrics = metrics
        self.audit = audit_logger
        self.logger = logger.bind(component="role_manager")
    
    async def create_role(self,
                         role: Role,
                         created_by: str) -> bool:
        """Create a new role."""
        try:
            # Check if role already exists
            if await self._role_exists(role.name):
                raise AuthError(f"Role {role.name} already exists")
            
            # Validate parent roles
            if role.parent_roles:
                for parent in role.parent_roles:
                    if not await self._role_exists(parent):
                        raise AuthError(f"Parent role {parent} does not exist")
            
            # Store role definition
            role_key = f"role:def:{role.name}"
            role_data = {
                "name": role.name,
                "policies": [vars(p) for p in role.policies],
                "parent_roles": role.parent_roles,
                "metadata": role.metadata,
                "created_by": created_by,
                "created_at": datetime.utcnow().isoformat()
            }
            
            await self.cache.set(role_key, json.dumps(role_data))
            self.metrics.increment("role_created")
            
            self.logger.info("role_created",
                           role=role.name,
                           created_by=created_by)
            return True
            
        except Exception as e:
            self.logger.error("role_creation_failed",
                            role=role.name,
                            error=str(e))
            raise
    
    async def assign_role(self,
                         assignment: RoleAssignment) -> bool:
        """Assign role to user."""
        try:
            # Validate role exists
            if not await self._role_exists(assignment.role_name):
                raise AuthError(f"Role {assignment.role_name} does not exist")
            
            # Store assignment
            assignment_key = f"role:assignment:{assignment.user_id}:{assignment.role_name}"
            assignment_data = {
                "user_id": assignment.user_id,
                "role_name": assignment.role_name,
                "assigned_by": assignment.assigned_by,
                "assigned_at": assignment.assigned_at.isoformat(),
                "expires_at": assignment.expires_at.isoformat() if assignment.expires_at else None,
                "metadata": assignment.metadata
            }
            
            await self.cache.set(assignment_key, json.dumps(assignment_data))
            
            # Update user's role cache
            await self._update_user_roles_cache(assignment.user_id)
            
            self.metrics.increment("role_assigned")
            self.logger.info("role_assigned",
                           user=assignment.user_id,
                           role=assignment.role_name,
                           assigned_by=assignment.assigned_by)
            
            return True
            
        except Exception as e:
            self.logger.error("role_assignment_failed",
                            user=assignment.user_id,
                            role=assignment.role_name,
                            error=str(e))
            raise
    
    async def revoke_role(self,
                         user_id: str,
                         role_name: str,
                         revoked_by: str) -> bool:
        """Revoke role from user."""
        try:
            # Remove assignment
            assignment_key = f"role:assignment:{user_id}:{role_name}"
            if not await self.cache.delete(assignment_key):
                return False
            
            # Update user's role cache
            await self._update_user_roles_cache(user_id)
            
            self.metrics.increment("role_revoked")
            self.logger.info("role_revoked",
                           user=user_id,
                           role=role_name,
                           revoked_by=revoked_by)
            
            return True
            
        except Exception as e:
            self.logger.error("role_revocation_failed",
                            user=user_id,
                            role=role_name,
                            error=str(e))
            raise
    
    async def get_user_roles(self, user_id: str) -> List[Role]:
        """Get all roles assigned to user."""
        try:
            # Try cache first
            cache_key = f"user:roles:{user_id}"
            cached = await self.cache.get(cache_key)
            if cached:
                return [Role(**r) for r in json.loads(cached)]
            
            # Rebuild from assignments
            pattern = f"role:assignment:{user_id}:*"
            assignments = await self.cache.scan(pattern)
            
            roles = []
            for assignment_key in assignments:
                assignment_data = json.loads(await self.cache.get(assignment_key))
                role = await self._get_role(assignment_data["role_name"])
                if role:
                    roles.append(role)
            
            # Update cache
            if roles:
                await self.cache.set(
                    cache_key,
                    json.dumps([vars(r) for r in roles]),
                    3600  # 1 hour TTL
                )
            
            return roles
            
        except Exception as e:
            self.logger.error("role_fetch_failed",
                            user=user_id,
                            error=str(e))
            raise
    
    async def _role_exists(self, role_name: str) -> bool:
        """Check if role exists."""
        role_key = f"role:def:{role_name}"
        return await self.cache.exists(role_key)
    
    async def _get_role(self, role_name: str) -> Optional[Role]:
        """Get role definition."""
        role_key = f"role:def:{role_name}"
        role_data = await self.cache.get(role_key)
        if role_data:
            data = json.loads(role_data)
            return Role(
                name=data["name"],
                policies=[ResourcePolicy(**p) for p in data["policies"]],
                parent_roles=data.get("parent_roles"),
                metadata=data.get("metadata")
            )
        return None
    
    async def _update_user_roles_cache(self, user_id: str):
        """Update user's roles cache."""
        cache_key = f"user:roles:{user_id}"
        await self.cache.delete(cache_key)
    
    async def create_role_with_audit(self,
                                   role: Role,
                                   created_by: str,
                                   ip_address: Optional[str] = None,
                                   session_id: Optional[str] = None) -> bool:
        """Create role with audit logging."""
        try:
            # Create role
            success = await self.create_role(role, created_by)
            
            # Log audit event
            await self.audit.log_role_event(
                AuditEvent(
                    event_type="role_creation",
                    actor_id=created_by,
                    resource_type="role",
                    resource_id=role.name,
                    action="create",
                    timestamp=datetime.utcnow(),
                    status="success" if success else "failure",
                    details={"policies": [vars(p) for p in role.policies]},
                    ip_address=ip_address,
                    session_id=session_id
                )
            )
            
            return success
            
        except Exception as e:
            # Log failure audit event
            await self.audit.log_role_event(
                AuditEvent(
                    event_type="role_creation",
                    actor_id=created_by,
                    resource_type="role",
                    resource_id=role.name,
                    action="create",
                    timestamp=datetime.utcnow(),
                    status="error",
                    details={"error": str(e)},
                    ip_address=ip_address,
                    session_id=session_id
                )
            )
            raise
    
    async def assign_role_with_audit(self,
                                   assignment: RoleAssignment,
                                   ip_address: Optional[str] = None,
                                   session_id: Optional[str] = None) -> bool:
        """Assign role with audit logging."""
        try:
            # Assign role
            success = await self.assign_role(assignment)
            
            # Log audit event
            await self.audit.log_role_event(
                AuditEvent(
                    event_type="role_assignment",
                    actor_id=assignment.assigned_by,
                    resource_type="role_assignment",
                    resource_id=f"{assignment.user_id}:{assignment.role_name}",
                    action="assign",
                    timestamp=datetime.utcnow(),
                    status="success" if success else "failure",
                    details={
                        "user_id": assignment.user_id,
                        "role_name": assignment.role_name,
                        "expires_at": assignment.expires_at.isoformat() if assignment.expires_at else None
                    },
                    ip_address=ip_address,
                    session_id=session_id
                )
            )
            
            return success
            
        except Exception as e:
            # Log failure audit event
            await self.audit.log_role_event(
                AuditEvent(
                    event_type="role_assignment",
                    actor_id=assignment.assigned_by,
                    resource_type="role_assignment",
                    resource_id=f"{assignment.user_id}:{assignment.role_name}",
                    action="assign",
                    timestamp=datetime.utcnow(),
                    status="error",
                    details={"error": str(e)},
                    ip_address=ip_address,
                    session_id=session_id
                )
            )
            raise 