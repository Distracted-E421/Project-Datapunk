from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Dict, Optional
from datetime import datetime
from .role_manager import RoleManager, RoleAssignment
from .core.access_control import Role, ResourcePolicy, Permission

router = APIRouter(prefix="/auth/roles", tags=["roles"])

async def get_role_manager() -> RoleManager:
    # Initialize and return RoleManager instance
    # This would be properly configured in your app startup
    pass

@router.post("/")
async def create_role(
    role: Role,
    created_by: str,
    role_manager: RoleManager = Depends(get_role_manager)
) -> Dict:
    """Create a new role."""
    try:
        success = await role_manager.create_role(role, created_by)
        return {"success": success, "role": role.name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/assign")
async def assign_role(
    user_id: str,
    role_name: str,
    assigned_by: str,
    expires_at: Optional[datetime] = None,
    metadata: Optional[Dict] = None,
    role_manager: RoleManager = Depends(get_role_manager)
) -> Dict:
    """Assign role to user."""
    try:
        assignment = RoleAssignment(
            user_id=user_id,
            role_name=role_name,
            assigned_by=assigned_by,
            assigned_at=datetime.utcnow(),
            expires_at=expires_at,
            metadata=metadata
        )
        success = await role_manager.assign_role(assignment)
        return {"success": success, "assignment": vars(assignment)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/revoke/{user_id}/{role_name}")
async def revoke_role(
    user_id: str,
    role_name: str,
    revoked_by: str,
    role_manager: RoleManager = Depends(get_role_manager)
) -> Dict:
    """Revoke role from user."""
    try:
        success = await role_manager.revoke_role(user_id, role_name, revoked_by)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user/{user_id}")
async def get_user_roles(
    user_id: str,
    role_manager: RoleManager = Depends(get_role_manager)
) -> Dict:
    """Get all roles assigned to user."""
    try:
        roles = await role_manager.get_user_roles(user_id)
        return {
            "user_id": user_id,
            "roles": [vars(r) for r in roles]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/audit")
async def create_role_with_audit(
    role: Role,
    created_by: str,
    request: Request,
    role_manager: RoleManager = Depends(get_role_manager)
) -> Dict:
    """Create a new role with audit logging."""
    try:
        success = await role_manager.create_role_with_audit(
            role,
            created_by,
            ip_address=request.client.host,
            session_id=request.session.get("session_id")
        )
        return {"success": success, "role": role.name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/audit/assign")
async def assign_role_with_audit(
    user_id: str,
    role_name: str,
    assigned_by: str,
    request: Request,
    expires_at: Optional[datetime] = None,
    metadata: Optional[Dict] = None,
    role_manager: RoleManager = Depends(get_role_manager)
) -> Dict:
    """Assign role with audit logging."""
    try:
        assignment = RoleAssignment(
            user_id=user_id,
            role_name=role_name,
            assigned_by=assigned_by,
            assigned_at=datetime.utcnow(),
            expires_at=expires_at,
            metadata=metadata
        )
        success = await role_manager.assign_role_with_audit(
            assignment,
            ip_address=request.client.host,
            session_id=request.session.get("session_id")
        )
        return {"success": success, "assignment": vars(assignment)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 