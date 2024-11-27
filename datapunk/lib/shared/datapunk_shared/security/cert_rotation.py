"""
Certificate Rotation Manager for Datapunk's Security Infrastructure

Implements automated certificate lifecycle management within the service mesh,
ensuring continuous service availability through proactive certificate rotation.

Key features:
- Automated certificate expiration monitoring
- Proactive rotation before expiration
- Metrics tracking for rotation operations
- Graceful error handling with metrics

Integration points:
- Works with CertificateManager for MTLS operations
- Reports metrics for monitoring and alerting
- Coordinates with service mesh for certificate distribution

NOTE: This component is critical for maintaining mesh security and 
should be monitored closely for any rotation failures.
"""

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
    """
    Manages proactive certificate rotation across the service mesh.
    
    Implements a window-based rotation strategy to ensure certificates
    are rotated before expiration, preventing service disruption.
    
    NOTE: Rotation window should be tuned based on service deployment
    frequency and certificate provisioning latency.
    """
    
    def __init__(self, 
                 cert_manager: CertificateManager,
                 metrics: MetricsClient,
                 rotation_window: int = 7):  # Days before expiry to rotate
        # FIXME: Consider making rotation_window configurable per service
        self.cert_manager = cert_manager
        self.metrics = metrics
        self.rotation_window = rotation_window
        self.logger = logger.bind(component="cert_rotation")
        
    async def check_and_rotate_certificates(self) -> None:
        """
        Checks all active certificates and rotates those approaching expiration.
        
        Critical operation that maintains service mesh security. Failures here
        could lead to service disruption if certificates expire.
        
        TODO: Add parallel rotation support for multiple certificates
        TODO: Implement rate limiting for rotation operations
        """
        try:
            certs = await self.cert_manager.list_active_certificates()
            for cert_info in certs:
                if await self._needs_rotation(cert_info):
                    await self._rotate_certificate(cert_info)
                    
        except Exception as e:
            # Rotation failures are critical and need immediate attention
            self.logger.error("certificate_rotation_failed", error=str(e))
            self.metrics.increment("cert_rotation_failures")
            raise
    
    async def _needs_rotation(self, cert_info: Dict) -> bool:
        """
        Determines if a certificate needs rotation based on expiration window.
        
        Returns True if:
        - Certificate is within rotation window of expiration
        - Certificate parsing fails (fail-safe approach)
        - Expiration date cannot be determined
        """
        try:
            cert = x509.load_pem_x509_certificate(cert_info["certificate"].encode())
            expiry = cert.not_valid_after
            rotation_date = expiry - timedelta(days=self.rotation_window)
            
            return datetime.utcnow() >= rotation_date
            
        except Exception as e:
            # Any cert parsing failure triggers rotation for safety
            self.logger.error("cert_check_failed", 
                            cert_id=cert_info.get("id"),
                            error=str(e))
            return True
    
    async def _rotate_certificate(self, cert_info: Dict) -> None:
        """
        Performs certificate rotation for a service.
        
        Critical operation that must maintain consistency:
        1. Generate new certificate
        2. Update service configuration
        3. Track metrics
        
        NOTE: Service may require restart to pick up new certificate
        depending on implementation.
        """
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