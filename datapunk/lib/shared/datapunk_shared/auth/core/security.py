"""
Core security components for auth system.

This module provides:
- Encryption management (symmetric/asymmetric)
- Key management (generation, rotation)
- Certificate management (mTLS)
- Security policy enforcement
"""

from typing import Dict, Optional, Any, TYPE_CHECKING
import structlog
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.x509 import load_pem_x509_certificate
import base64
import os

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....cache import CacheClient
    from ....messaging import MessageBroker

logger = structlog.get_logger()

class EncryptionManager:
    """Handles encryption operations."""
    
    def __init__(self,
                 metrics: 'MetricsClient',
                 key_rotation_interval: timedelta = timedelta(days=30)):
        self.metrics = metrics
        self.rotation_interval = key_rotation_interval
        self.logger = logger.bind(component="encryption")
        self._fernet = None
        self._last_rotation = None
    
    async def initialize(self) -> None:
        """Initialize encryption system."""
        try:
            await self._rotate_keys()
        except Exception as e:
            self.logger.error("encryption_init_failed",
                            error=str(e))
            raise
    
    async def encrypt(self, data: bytes) -> bytes:
        """Encrypt data using current key."""
        try:
            if self._needs_rotation():
                await self._rotate_keys()
            
            encrypted = self._fernet.encrypt(data)
            
            self.metrics.increment("encryption_operations",
                                 {"operation": "encrypt"})
            
            return encrypted
            
        except Exception as e:
            self.logger.error("encryption_failed",
                            error=str(e))
            self.metrics.increment("encryption_errors")
            raise
    
    async def decrypt(self, data: bytes) -> bytes:
        """Decrypt data."""
        try:
            decrypted = self._fernet.decrypt(data)
            
            self.metrics.increment("encryption_operations",
                                 {"operation": "decrypt"})
            
            return decrypted
            
        except Exception as e:
            self.logger.error("decryption_failed",
                            error=str(e))
            self.metrics.increment("decryption_errors")
            raise
    
    def _needs_rotation(self) -> bool:
        """Check if key rotation is needed."""
        if not self._last_rotation:
            return True
        return datetime.utcnow() - self._last_rotation >= self.rotation_interval
    
    async def _rotate_keys(self) -> None:
        """Rotate encryption keys."""
        try:
            new_key = Fernet.generate_key()
            self._fernet = Fernet(new_key)
            self._last_rotation = datetime.utcnow()
            
            self.metrics.increment("key_rotations")
            self.logger.info("encryption_keys_rotated")
            
        except Exception as e:
            self.logger.error("key_rotation_failed",
                            error=str(e))
            raise

class CertificateManager:
    """Manages service certificates for mTLS."""
    
    def __init__(self,
                 metrics: 'MetricsClient',
                 cert_dir: str = "/etc/certs",
                 cert_validity: timedelta = timedelta(days=365)):
        self.metrics = metrics
        self.cert_dir = cert_dir
        self.cert_validity = cert_validity
        self.logger = logger.bind(component="certificates")
    
    async def generate_service_cert(self,
                                  service_name: str,
                                  common_name: str) -> Dict[str, str]:
        """Generate service certificate and private key."""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Generate certificate
            # Implementation would create proper X.509 cert
            # This is a placeholder
            
            self.metrics.increment("certificates_generated",
                                 {"service": service_name})
            
            return {
                "cert_path": f"{self.cert_dir}/{service_name}.crt",
                "key_path": f"{self.cert_dir}/{service_name}.key"
            }
            
        except Exception as e:
            self.logger.error("cert_generation_failed",
                            service=service_name,
                            error=str(e))
            raise
    
    async def validate_cert(self,
                          cert_path: str,
                          service_name: str) -> bool:
        """Validate service certificate."""
        try:
            with open(cert_path, 'rb') as f:
                cert_data = f.read()
            
            cert = load_pem_x509_certificate(cert_data)
            
            # Validate certificate
            # Implementation would check validity, CN, etc
            # This is a placeholder
            
            return True
            
        except Exception as e:
            self.logger.error("cert_validation_failed",
                            service=service_name,
                            error=str(e))
            return False

class SecurityManager:
    """Central security management."""
    
    def __init__(self,
                 metrics: 'MetricsClient',
                 cache: 'CacheClient',
                 message_broker: 'MessageBroker'):
        self.metrics = metrics
        self.cache = cache
        self.broker = message_broker
        self.logger = logger.bind(component="security")
        
        self.encryption = EncryptionManager(metrics)
        self.certificates = CertificateManager(metrics)
    
    async def initialize(self) -> None:
        """Initialize security components."""
        try:
            await self.encryption.initialize()
            
            # Set up security event monitoring
            await self._setup_monitoring()
            
            self.logger.info("security_manager_initialized")
            
        except Exception as e:
            self.logger.error("security_init_failed",
                            error=str(e))
            raise
    
    async def setup_mtls(self,
                        service_name: str,
                        common_name: str) -> Dict[str, str]:
        """Set up mutual TLS for a service."""
        try:
            # Generate service certificates
            cert_paths = await self.certificates.generate_service_cert(
                service_name,
                common_name
            )
            
            # Store certificate info
            await self._store_cert_info(
                service_name,
                cert_paths
            )
            
            return cert_paths
            
        except Exception as e:
            self.logger.error("mtls_setup_failed",
                            service=service_name,
                            error=str(e))
            raise
    
    async def rotate_service_certs(self,
                                 service_name: str) -> Dict[str, str]:
        """Handle service certificate rotation."""
        try:
            # Get existing cert info
            cert_info = await self._get_cert_info(service_name)
            
            # Generate new certificates
            new_cert_paths = await self.certificates.generate_service_cert(
                service_name,
                cert_info["common_name"]
            )
            
            # Update stored info
            await self._store_cert_info(
                service_name,
                new_cert_paths
            )
            
            # Notify about rotation
            await self._notify_cert_rotation(
                service_name,
                new_cert_paths
            )
            
            return new_cert_paths
            
        except Exception as e:
            self.logger.error("cert_rotation_failed",
                            service=service_name,
                            error=str(e))
            raise
    
    async def _setup_monitoring(self) -> None:
        """Set up security monitoring."""
        # Implementation would set up security event monitoring
        # This is a placeholder
        pass
    
    async def _store_cert_info(self,
                              service_name: str,
                              cert_paths: Dict[str, str]) -> None:
        """Store certificate information."""
        key = f"security:certs:{service_name}"
        await self.cache.set(key, {
            "paths": cert_paths,
            "updated_at": datetime.utcnow().isoformat()
        })
    
    async def _get_cert_info(self, service_name: str) -> Optional[Dict]:
        """Get stored certificate information."""
        key = f"security:certs:{service_name}"
        return await self.cache.get(key)
    
    async def _notify_cert_rotation(self,
                                  service_name: str,
                                  new_paths: Dict[str, str]) -> None:
        """Notify about certificate rotation."""
        await self.broker.publish(
            "security.cert_rotation",
            {
                "service": service_name,
                "new_paths": new_paths,
                "timestamp": datetime.utcnow().isoformat()
            }
        ) 