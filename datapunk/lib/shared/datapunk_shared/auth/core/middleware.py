from typing import Dict, Optional, TYPE_CHECKING
from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
import structlog

from .access_control import AccessManager, Permission

if TYPE_CHECKING:
    from ...monitoring import MetricsClient

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