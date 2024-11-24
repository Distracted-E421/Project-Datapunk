from typing import Optional, Dict, Tuple
import ssl
import OpenSSL
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from datetime import datetime, timedelta
import structlog
from pathlib import Path
import aiohttp
import asyncio
from dataclasses import dataclass

logger = structlog.get_logger()

@dataclass
class MTLSConfig:
    """Configuration for mTLS."""
    cert_path: str
    key_path: str
    ca_path: str
    verify_mode: ssl.VerifyMode = ssl.CERT_REQUIRED
    check_hostname: bool = True
    cert_reqs: int = ssl.CERT_REQUIRED
    cert_validity_days: int = 365
    key_size: int = 2048

class CertificateManager:
    """Manages certificate generation and validation."""
    
    def __init__(self, config: MTLSConfig):
        self.config = config
        self.logger = logger.bind(component="certificate_manager")
        
    def generate_private_key(self) -> RSAPrivateKey:
        """Generate RSA private key."""
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.config.key_size
        )
    
    def generate_certificate(self,
                           private_key: RSAPrivateKey,
                           common_name: str,
                           organization: str = "Datapunk",
                           country: str = "US") -> x509.Certificate:
        """Generate X.509 certificate."""
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=self.config.cert_validity_days)
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True
        ).sign(private_key, hashes.SHA256())
        
        return cert
    
    def save_certificate(self,
                        cert: x509.Certificate,
                        private_key: RSAPrivateKey,
                        cert_path: str,
                        key_path: str):
        """Save certificate and private key to files."""
        # Create directories if they don't exist
        Path(cert_path).parent.mkdir(parents=True, exist_ok=True)
        Path(key_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save certificate
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Save private key
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
    
    def load_certificate(self, cert_path: str) -> x509.Certificate:
        """Load certificate from file."""
        with open(cert_path, "rb") as f:
            return x509.load_pem_x509_certificate(f.read())
    
    def create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for mTLS."""
        ssl_context = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=self.config.ca_path
        )
        
        ssl_context.load_cert_chain(
            certfile=self.config.cert_path,
            keyfile=self.config.key_path
        )
        
        ssl_context.verify_mode = self.config.verify_mode
        ssl_context.check_hostname = self.config.check_hostname
        
        return ssl_context

class MTLSClient:
    """Client for making mTLS requests."""
    
    def __init__(self, config: MTLSConfig):
        self.config = config
        self.cert_manager = CertificateManager(config)
        self.logger = logger.bind(component="mtls_client")
        
    async def request(self,
                     method: str,
                     url: str,
                     **kwargs) -> Tuple[int, Dict]:
        """Make mTLS request."""
        ssl_context = self.cert_manager.create_ssl_context()
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method,
                    url,
                    ssl=ssl_context,
                    **kwargs
                ) as response:
                    return response.status, await response.json()
                    
            except Exception as e:
                self.logger.error("mtls_request_failed",
                                url=url,
                                error=str(e))
                raise

class MTLSServer:
    """Server-side mTLS handler."""
    
    def __init__(self, config: MTLSConfig):
        self.config = config
        self.cert_manager = CertificateManager(config)
        self.logger = logger.bind(component="mtls_server")
        
    def get_ssl_context(self) -> ssl.SSLContext:
        """Get SSL context for server."""
        return self.cert_manager.create_ssl_context()
    
    def verify_client_cert(self, cert: x509.Certificate) -> bool:
        """Verify client certificate."""
        try:
            # Load CA certificate
            with open(self.config.ca_path, "rb") as f:
                ca_cert = x509.load_pem_x509_certificate(f.read())
            
            # Verify certificate
            ca_public_key = ca_cert.public_key()
            ca_public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding=None,
                algorithm=cert.signature_hash_algorithm
            )
            
            return True
            
        except Exception as e:
            self.logger.error("client_cert_verification_failed",
                            error=str(e))
            return False 