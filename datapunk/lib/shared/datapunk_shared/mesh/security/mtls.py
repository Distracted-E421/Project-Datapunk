from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
import ssl
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import OpenSSL
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from ..monitoring import MetricsCollector

@dataclass
class MTLSConfig:
    """Configuration for mutual TLS"""
    ca_cert: str
    certificate: str
    private_key: str
    verify_mode: ssl.VerifyMode = ssl.CERT_REQUIRED
    cert_reqs: ssl.VerifyMode = ssl.CERT_REQUIRED
    check_hostname: bool = True
    ciphers: str = "ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
    cert_store_path: Optional[str] = None
    cert_validity_days: int = 365
    key_size: int = 2048
    auto_renewal: bool = True
    renewal_threshold_days: int = 30

class MTLSError(Exception):
    """Base class for MTLS errors"""
    pass

class CertificateError(MTLSError):
    """Certificate-related errors"""
    pass

class MTLSManager:
    """Manages mutual TLS certificates and configuration"""
    def __init__(
        self,
        config: MTLSConfig,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.metrics = metrics_collector
        self._ssl_context = None
        self._cert_info: Dict[str, Any] = {}
        self._renewal_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize MTLS manager"""
        try:
            # Load and validate certificates
            await self._load_certificates()
            
            # Start certificate renewal task if enabled
            if self.config.auto_renewal:
                self._renewal_task = asyncio.create_task(self._certificate_renewal_loop())

            if self.metrics:
                await self.metrics.increment("mtls.initialization.success")

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "mtls.initialization.error",
                    tags={"error": str(e)}
                )
            raise MTLSError(f"Failed to initialize MTLS: {str(e)}")

    async def stop(self):
        """Stop MTLS manager"""
        if self._renewal_task:
            self._renewal_task.cancel()
            try:
                await self._renewal_task
            except asyncio.CancelledError:
                pass

    def get_ssl_context(self) -> ssl.SSLContext:
        """Get SSL context for MTLS"""
        if not self._ssl_context:
            self._ssl_context = self._create_ssl_context()
        return self._ssl_context

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with MTLS configuration"""
        try:
            context = ssl.create_default_context(
                purpose=ssl.Purpose.CLIENT_AUTH,
                cafile=self.config.ca_cert
            )
            
            context.load_cert_chain(
                certfile=self.config.certificate,
                keyfile=self.config.private_key
            )
            
            context.verify_mode = self.config.verify_mode
            context.check_hostname = self.config.check_hostname
            
            if self.config.ciphers:
                context.set_ciphers(self.config.ciphers)

            return context

        except Exception as e:
            raise MTLSError(f"Failed to create SSL context: {str(e)}")

    async def _load_certificates(self):
        """Load and validate certificates"""
        try:
            # Load CA certificate
            with open(self.config.ca_cert, 'rb') as f:
                ca_cert = x509.load_pem_x509_certificate(f.read())
            
            # Load service certificate
            with open(self.config.certificate, 'rb') as f:
                cert = x509.load_pem_x509_certificate(f.read())
            
            # Store certificate info
            self._cert_info = {
                "ca_not_before": ca_cert.not_valid_before,
                "ca_not_after": ca_cert.not_valid_after,
                "cert_not_before": cert.not_valid_before,
                "cert_not_after": cert.not_valid_after,
                "subject": cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value,
                "issuer": cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            }

            # Validate certificates
            await self._validate_certificates()

        except Exception as e:
            raise CertificateError(f"Failed to load certificates: {str(e)}")

    async def _validate_certificates(self):
        """Validate loaded certificates"""
        now = datetime.utcnow()
        
        # Check certificate validity
        if now < self._cert_info["cert_not_before"]:
            raise CertificateError("Certificate not yet valid")
            
        if now > self._cert_info["cert_not_after"]:
            raise CertificateError("Certificate has expired")
            
        # Check CA certificate validity
        if now < self._cert_info["ca_not_before"]:
            raise CertificateError("CA certificate not yet valid")
            
        if now > self._cert_info["ca_not_after"]:
            raise CertificateError("CA certificate has expired")

        if self.metrics:
            await self.metrics.gauge(
                "mtls.certificate.days_until_expiry",
                (self._cert_info["cert_not_after"] - now).days
            )

    async def _certificate_renewal_loop(self):
        """Periodic certificate renewal check"""
        while True:
            try:
                await asyncio.sleep(24 * 60 * 60)  # Check daily
                await self._check_certificate_renewal()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "mtls.renewal.error",
                        tags={"error": str(e)}
                    )

    async def _check_certificate_renewal(self):
        """Check if certificate needs renewal"""
        now = datetime.utcnow()
        days_until_expiry = (self._cert_info["cert_not_after"] - now).days
        
        if days_until_expiry <= self.config.renewal_threshold_days:
            try:
                await self.renew_certificate()
                if self.metrics:
                    await self.metrics.increment("mtls.certificate.renewed")
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "mtls.renewal.error",
                        tags={"error": str(e)}
                    )
                raise

    async def renew_certificate(self):
        """Renew service certificate"""
        try:
            # Generate new key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.config.key_size
            )
            
            # Create certificate signing request (CSR)
            csr = x509.CertificateSigningRequestBuilder().subject_name(
                x509.Name([
                    x509.NameAttribute(NameOID.COMMON_NAME, self._cert_info["subject"])
                ])
            ).sign(private_key, hashes.SHA256())
            
            # Save private key
            with open(self.config.private_key, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Save CSR (for manual signing if needed)
            csr_path = Path(self.config.certificate).with_suffix('.csr')
            with open(csr_path, 'wb') as f:
                f.write(csr.public_bytes(serialization.Encoding.PEM))
            
            # Here you would typically send the CSR to your CA for signing
            # For now, we'll just indicate that manual intervention is needed
            raise NotImplementedError(
                f"Certificate renewal requires manual signing of CSR at {csr_path}"
            )

        except Exception as e:
            raise CertificateError(f"Failed to renew certificate: {str(e)}")

    async def get_certificate_info(self) -> Dict[str, Any]:
        """Get information about current certificates"""
        now = datetime.utcnow()
        return {
            **self._cert_info,
            "days_until_expiry": (self._cert_info["cert_not_after"] - now).days,
            "needs_renewal": (self._cert_info["cert_not_after"] - now).days <= self.config.renewal_threshold_days
        }

    def verify_peer_certificate(self, cert_der: bytes) -> bool:
        """Verify peer certificate"""
        try:
            cert = x509.load_der_x509_certificate(cert_der)
            
            # Basic validation
            now = datetime.utcnow()
            if now < cert.not_valid_before or now > cert.not_valid_after:
                return False
                
            # Additional validation could be added here
            # - Check certificate chain
            # - Check revocation status
            # - Check custom policies
            
            return True
            
        except Exception:
            return False