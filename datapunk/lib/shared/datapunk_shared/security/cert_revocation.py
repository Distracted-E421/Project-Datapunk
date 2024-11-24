from typing import Optional, List, Dict
import asyncio
from datetime import datetime
import structlog
from cryptography import x509
from cryptography.x509 import CertificateRevocationList
from cryptography.hazmat.primitives import hashes
from .mtls import CertificateManager
from ..cache import CacheClient

logger = structlog.get_logger()

class CertificateRevocationManager:
    """Manages certificate revocation."""
    
    def __init__(self,
                 cert_manager: CertificateManager,
                 cache_client: CacheClient):
        self.cert_manager = cert_manager
        self.cache = cache_client
        self.logger = logger.bind(component="cert_revocation")
        self.crl_cache_key = "cert:crl:latest"
        
    async def revoke_certificate(self,
                               cert_id: str,
                               reason: str = "unspecified") -> None:
        """Revoke a certificate."""
        try:
            # Get certificate details
            cert_info = await self.cert_manager.get_certificate(cert_id)
            if not cert_info:
                raise ValueError(f"Certificate {cert_id} not found")
            
            # Add to CRL
            await self._add_to_crl(cert_info, reason)
            
            # Invalidate service certificate
            await self.cert_manager.invalidate_service_cert(
                cert_info.get("service_name"),
                cert_id
            )
            
            # Update revocation cache
            await self._update_revocation_cache(cert_id)
            
            self.logger.info("certificate_revoked",
                           cert_id=cert_id,
                           reason=reason)
            
        except Exception as e:
            self.logger.error("certificate_revocation_failed",
                            cert_id=cert_id,
                            error=str(e))
            raise
    
    async def check_revocation(self, cert: x509.Certificate) -> bool:
        """Check if a certificate is revoked."""
        try:
            cert_id = cert.serial_number
            
            # Check cache first
            if await self._is_revoked_in_cache(str(cert_id)):
                return True
            
            # Check CRL
            crl = await self._get_current_crl()
            return self._is_in_crl(cert, crl)
            
        except Exception as e:
            self.logger.error("revocation_check_failed",
                            error=str(e))
            # Fail closed - treat errors as revoked
            return True
    
    async def _add_to_crl(self,
                         cert_info: Dict,
                         reason: str) -> None:
        """Add certificate to CRL."""
        crl = await self._get_current_crl()
        new_crl = await self.cert_manager.update_crl(
            crl,
            cert_info,
            reason
        )
        await self._store_crl(new_crl)
    
    async def _update_revocation_cache(self, cert_id: str) -> None:
        """Update revocation cache."""
        cache_key = f"cert:revoked:{cert_id}"
        await self.cache.set(cache_key, "1", expire=86400)  # 24h TTL
    
    async def _is_revoked_in_cache(self, cert_id: str) -> bool:
        """Check if certificate is revoked in cache."""
        cache_key = f"cert:revoked:{cert_id}"
        return await self.cache.exists(cache_key)
    
    async def _get_current_crl(self) -> CertificateRevocationList:
        """Get current CRL."""
        crl_pem = await self.cache.get(self.crl_cache_key)
        if not crl_pem:
            crl = await self.cert_manager.get_crl()
            await self._store_crl(crl)
            return crl
        return self.cert_manager.load_crl(crl_pem)
    
    async def _store_crl(self, crl: CertificateRevocationList) -> None:
        """Store CRL in cache."""
        crl_pem = self.cert_manager.serialize_crl(crl)
        await self.cache.set(self.crl_cache_key, crl_pem, expire=3600)  # 1h TTL
    
    def _is_in_crl(self,
                   cert: x509.Certificate,
                   crl: CertificateRevocationList) -> bool:
        """Check if certificate is in CRL."""
        return cert.serial_number in [
            revoked.serial_number
            for revoked in crl
        ] 