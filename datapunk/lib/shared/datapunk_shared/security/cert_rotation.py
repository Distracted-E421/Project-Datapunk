from typing import Optional, Dict, List
import asyncio
from datetime import datetime, timedelta
import structlog
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from .mtls import CertificateManager, MTLSConfig
from ..monitoring import MetricsClient

logger = structlog.get_logger()

class CertificateRotationManager:
    """Manages automatic certificate rotation."""
    
    def __init__(self, 
                 cert_manager: CertificateManager,
                 metrics: MetricsClient,
                 rotation_window: int = 7):  # Days before expiry to rotate
        self.cert_manager = cert_manager
        self.metrics = metrics
        self.rotation_window = rotation_window
        self.logger = logger.bind(component="cert_rotation")
        
    async def check_and_rotate_certificates(self) -> None:
        """Check certificates and rotate if needed."""
        try:
            certs = await self.cert_manager.list_active_certificates()
            for cert_info in certs:
                if await self._needs_rotation(cert_info):
                    await self._rotate_certificate(cert_info)
                    
        except Exception as e:
            self.logger.error("certificate_rotation_failed", error=str(e))
            self.metrics.increment("cert_rotation_failures")
            raise
    
    async def _needs_rotation(self, cert_info: Dict) -> bool:
        """Check if certificate needs rotation."""
        try:
            cert = x509.load_pem_x509_certificate(cert_info["certificate"].encode())
            expiry = cert.not_valid_after
            rotation_date = expiry - timedelta(days=self.rotation_window)
            
            return datetime.utcnow() >= rotation_date
            
        except Exception as e:
            self.logger.error("cert_check_failed", 
                            cert_id=cert_info.get("id"),
                            error=str(e))
            return True
    
    async def _rotate_certificate(self, cert_info: Dict) -> None:
        """Rotate a certificate."""
        service_name = cert_info.get("service_name")
        cert_id = cert_info.get("id")
        
        try:
            # Generate new certificate
            new_cert = await self.cert_manager.generate_certificate(
                service_name,
                cert_info.get("common_name")
            )
            
            # Update service configuration
            await self.cert_manager.update_service_cert(
                service_name,
                new_cert,
                cert_info.get("current_cert")
            )
            
            self.logger.info("certificate_rotated",
                           service=service_name,
                           cert_id=cert_id)
            self.metrics.increment("cert_rotations_success")
            
        except Exception as e:
            self.logger.error("certificate_rotation_failed",
                            service=service_name,
                            cert_id=cert_id,
                            error=str(e))
            self.metrics.increment("cert_rotation_failures")
            raise 