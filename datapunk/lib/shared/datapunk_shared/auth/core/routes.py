from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, List, Optional
from datetime import datetime
import structlog

from .access_control import AccessManager, Role, ResourcePolicy
from .validation import CoreValidator, ValidationConfig
from .types import RoleConfig, ValidationResult
from .exceptions import AuthError, InvalidRoleError

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])

async def get_access_manager() -> AccessManager:
    """Dependency injection for AccessManager."""
    # This would be properly configured in your app startup
    pass

async def get_validator() -> CoreValidator:
    """Dependency injection for CoreValidator."""
    # This would be properly configured in your app startup
    pass

@router.post("/roles", response_model=Dict)
async def create_role(
    role: Role,
    request: Request,
    access_manager: AccessManager = Depends(get_access_manager),
    validator: CoreValidator = Depends(get_validator)
) -> Dict:
    """Create a new role."""
    try:
        # Validate role configuration
        validation_result = await validator.validate_role(role)
        if not validation_result["valid"]:
            raise InvalidRoleError(
                role.name,
                "Validation failed",
                {"issues": validation_result["issues"]}
            )
        
        # Create role
        success = await access_manager.create_role(
            role,
            created_by=request.state.user_id,
            ip_address=request.client.host,
            session_id=request.session.get("session_id")
        )
        
        return {
            "success": success,
            "role": role.name,
            "validation": validation_result
        }
        
    except AuthError as e:
        logger.error("role_creation_failed",
                    role=role.name,
                    error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("unexpected_error",
                    error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/roles/{role_name}/policies", response_model=List[Dict])
async def get_role_policies(
    role_name: str,
    access_manager: AccessManager = Depends(get_access_manager)
) -> List[Dict]:
    """Get policies for a role."""
    try:
        role = await access_manager.get_role(role_name)
        if not role:
            raise HTTPException(status_code=404, detail=f"Role {role_name} not found")
        
        return [vars(p) for p in role.policies]
        
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e)) 