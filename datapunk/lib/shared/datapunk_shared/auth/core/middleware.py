from typing import Dict, Optional, TYPE_CHECKING
from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
import structlog

from .access_control import AccessManager, Permission

if TYPE_CHECKING:
    from ...monitoring import MetricsClient

# Configure structured logging for consistent log format across the application
logger = structlog.get_logger()

class AccessControlMiddleware(BaseHTTPMiddleware):
    """Middleware for enforcing role-based access control (RBAC) in FastAPI applications.
    
    This middleware intercepts incoming requests and validates user permissions against
    defined route requirements. It integrates with the AccessManager for permission checks
    and supports path exemptions for public endpoints.
    
    Security Considerations:
    - Ensures consistent access control across all protected routes
    - Prevents unauthorized access through centralized permission validation
    - Supports audit logging of access attempts
    
    Performance Impact:
    - Adds minimal overhead as permission checks are performed in memory
    - Caching may be implemented in AccessManager for frequently accessed permissions
    """
    
    def __init__(self,
                 app,
                 access_manager: AccessManager,
                 route_permissions: Dict[str, Permission],
                 exempt_paths: Optional[List[str]] = None):
        """Initialize the access control middleware.
        
        Args:
            app: The FastAPI application instance
            access_manager: Service for managing and validating permissions
            route_permissions: Mapping of route paths to required permissions
            exempt_paths: List of paths that bypass access control (defaults to health/metrics)
        
        Note:
            Health and metrics endpoints are exempted by default to ensure monitoring 
            systems maintain access during potential auth issues.
        """
        super().__init__(app)
        self.access_manager = access_manager
        self.route_permissions = route_permissions
        self.exempt_paths = exempt_paths or ["/health", "/metrics"]
        # Bind component name to logger for easier log filtering and debugging
        self.logger = logger.bind(component="access_middleware") 