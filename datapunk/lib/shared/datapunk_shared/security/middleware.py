"""
MTLS Middleware for Datapunk's Service Mesh Security

Implements mutual TLS authentication at the FastAPI middleware level,
providing service-to-service authentication within the mesh.

Key features:
- Certificate-based mutual authentication
- Certificate validation and verification
- Request state enrichment with certificate info
- Structured logging for security events

Security considerations:
- Fails closed on any certificate issues
- Enforces strict certificate requirements
- Maintains audit trail through structured logging

NOTE: This middleware is a critical security component and should be
the first middleware in the chain to ensure all requests are authenticated
before any processing occurs.
"""

from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from .mtls import MTLSConfig, CertificateManager
import structlog
from typing import Optional

logger = structlog.get_logger()

class MTLSMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware implementing mutual TLS authentication.
    
    Ensures all service-to-service communication is authenticated via
    valid certificates. Integrates with CertificateManager for validation
    and maintains security context through request state.
    
    NOTE: Requires proper SSL/TLS termination configuration at the
    infrastructure level to access client certificates.
    """
    
    def __init__(self, app, config: MTLSConfig):
        super().__init__(app)
        self.config = config
        self.cert_manager = CertificateManager(config)
        self.logger = logger.bind(component="mtls_middleware")
    
    async def dispatch(self, request: Request, call_next):
        """
        Handles MTLS verification for each request.
        
        Critical security flow:
        1. Extract client certificate
        2. Verify certificate validity
        3. Enrich request state
        4. Forward to next handler
        
        Fails closed (403) on any certificate issues to maintain security.
        """
        client_cert = self._get_client_cert(request)
        if not client_cert:
            # FIXME: Add detailed error codes for different failure modes
            raise HTTPException(status_code=403,
                              detail="Client certificate required")
        
        if not self.cert_manager.verify_client_cert(client_cert):
            self.logger.warning("invalid_client_cert",
                              client_ip=request.client.host)
            raise HTTPException(status_code=403,
                              detail="Invalid client certificate")
        
        # Add certificate info to request state for downstream handlers
        # TODO: Consider adding certificate metadata (issuer, expiry, etc.)
        request.state.client_cert = client_cert
        
        response = await call_next(request)
        return response
    
    def _get_client_cert(self, request: Request) -> Optional[bytes]:
        """
        Extracts client certificate from request.
        
        Handles various ASGI server implementations that may store the
        certificate in different locations. Currently supports:
        - Direct SSL object access
        - Transport extra info
        
        NOTE: Some ASGI servers may require custom configuration to
        expose client certificates.
        """
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