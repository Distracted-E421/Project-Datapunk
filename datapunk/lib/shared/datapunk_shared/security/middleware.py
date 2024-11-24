from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from .mtls import MTLSConfig, CertificateManager
import structlog
from typing import Optional

logger = structlog.get_logger()

class MTLSMiddleware(BaseHTTPMiddleware):
    """Middleware for mTLS authentication."""
    
    def __init__(self, app, config: MTLSConfig):
        super().__init__(app)
        self.config = config
        self.cert_manager = CertificateManager(config)
        self.logger = logger.bind(component="mtls_middleware")
    
    async def dispatch(self, request: Request, call_next):
        """Handle mTLS verification."""
        client_cert = self._get_client_cert(request)
        if not client_cert:
            raise HTTPException(status_code=403,
                              detail="Client certificate required")
        
        if not self.cert_manager.verify_client_cert(client_cert):
            raise HTTPException(status_code=403,
                              detail="Invalid client certificate")
        
        # Add certificate info to request state
        request.state.client_cert = client_cert
        
        response = await call_next(request)
        return response
    
    def _get_client_cert(self, request: Request) -> Optional[bytes]:
        """Extract client certificate from request."""
        try:
            transport = request.scope.get("transport")
            if transport and hasattr(transport, "get_extra_info"):
                ssl_object = transport.get_extra_info("ssl_object")
                if ssl_object:
                    return ssl_object.getpeercert(binary_form=True)
        except Exception as e:
            self.logger.error("client_cert_extraction_failed",
                            error=str(e))
        return None 