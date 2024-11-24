from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict, List
from .access_control import AccessManager, Permission
import structlog
from datetime import datetime

logger = structlog.get_logger()

class AccessControlMiddleware(BaseHTTPMiddleware):
    """Middleware for enforcing access control."""
    
    def __init__(self,
                 app,
                 access_manager: AccessManager,
                 route_permissions: Dict[str, Permission],
                 exempt_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.access_manager = access_manager
        self.route_permissions = route_permissions
        self.exempt_paths = exempt_paths or ["/health", "/metrics"]
        self.logger = logger.bind(component="access_middleware")
    
    async def dispatch(self, request: Request, call_next):
        """Handle access control for request."""
        # Skip exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        try:
            # Get user from request (assuming auth middleware has run)
            user_id = request.state.user_id
            if not user_id:
                raise HTTPException(status_code=401, detail="Unauthorized")
            
            # Get required permission for route
            permission = self.route_permissions.get(request.url.path)
            if not permission:
                self.logger.warning("no_permission_defined",
                                  path=request.url.path)
                permission = Permission.READ  # Default to read
            
            # Build context for ABAC
            context = {
                "method": request.method,
                "path": request.url.path,
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "client_ip": request.client.host,
                "time": datetime.utcnow().isoformat()
            }
            
            # Check permission
            has_permission = await self.access_manager.check_permission(
                user_id=user_id,
                resource_type=request.url.path.split("/")[1],  # First path segment
                action=permission,
                context=context
            )
            
            if not has_permission:
                raise HTTPException(status_code=403, detail="Forbidden")
            
            return await call_next(request)
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error("access_control_failed",
                            path=request.url.path,
                            error=str(e))
            raise HTTPException(status_code=500, detail="Internal server error") 